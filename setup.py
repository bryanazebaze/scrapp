#!/usr/bin/env python3
"""CentralImmo — Python-based setup and management script.

This script handles the Python-level setup tasks that are needed on the
production server. It can be run independently or called by setup.sh.

Usage:
    python setup.py install        Create venv + install all dependencies
    python setup.py check          Verify database connection and .env config
    python setup.py restore        Restore the database dump
    python setup.py migrate        Run Alembic migrations
    python setup.py info           Print configuration summary

All commands are safe to run multiple times (idempotent).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve paths relative to this script's location.
# When deployed, setup.py lives in /opt/centralimmo/ alongside the app code.
# During development, it lives in the scrapp/ repo root.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DEPLOY_DIR = PROJECT_ROOT / "deploy"
VENV_DIR = PROJECT_ROOT / "venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
DUMP_FILE = DEPLOY_DIR / "immo_db_backup.dump"
SQL_DUMP_FILE = DEPLOY_DIR / "immo_db_backup.sql"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, printing it first. Raises on non-zero exit."""
    print(f"  -> {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


# ---------------------------------------------------------------------------
# Command: install
# ---------------------------------------------------------------------------
def cmd_install(args: argparse.Namespace) -> None:
    """Create a Python virtual environment and install all dependencies."""
    print("=== CentralImmo: Install Python environment ===\n")

    # 1. Create virtual environment
    if not (VENV_DIR / "bin" / "python").exists():
        print("[1/3] Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True, clear=False)
        print(f"  -> venv created at {VENV_DIR}")
    else:
        print(f"[1/3] Virtual environment already exists at {VENV_DIR}")

    # 2. Upgrade pip
    pip = str(VENV_DIR / "bin" / "pip")
    print("[2/3] Upgrading pip, setuptools, wheel...")
    run([pip, "install", "--upgrade", "pip", "setuptools", "wheel", "-q"])

    # 3. Install project dependencies
    if REQUIREMENTS_FILE.exists():
        print(f"[3/3] Installing dependencies from {REQUIREMENTS_FILE}...")
        run([pip, "install", "-r", str(REQUIREMENTS_FILE)])
        print("  -> Dependencies installed.")
    else:
        print(f"[3/3] WARNING: {REQUIREMENTS_FILE} not found, skipping.")
        print("  -> You may need to install dependencies manually.")

    print("\nEnvironment ready. Activate with:")
    print(f"  source {VENV_DIR}/bin/activate")
    print(f"  Or use the venv Python directly: {VENV_DIR}/bin/python")


# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> None:
    """Verify the environment is correctly configured."""
    print("=== CentralImmo: Environment Check ===\n")
    all_ok = True

    # 1. .env file
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print(f"[OK] .env found at {env_file}")
    else:
        print(f"[MISSING] .env not found at {env_file}")
        print("  Create one with: cp .env.example .env  (and edit values)")
        all_ok = False

    # 2. Virtual environment
    python = VENV_DIR / "bin" / "python"
    if python.exists():
        print(f"[OK] venv Python: {python}")
    else:
        print(f"[MISSING] venv not found. Run: python setup.py install")
        all_ok = False

    # 3. Import core packages
    if python.exists():
        for pkg in ["fastapi", "uvicorn", "sqlalchemy", "psycopg2", "pydantic"]:
            try:
                result = subprocess.run(
                    [str(python), "-c", f"import {pkg}"],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    print(f"[OK] Package '{pkg}' importable")
                else:
                    print(f"[FAIL] Package '{pkg}' not installed")
                    all_ok = False
            except FileNotFoundError:
                print(f"[FAIL] Cannot run Python from venv")
                all_ok = False
                break

    # 4. Database connection
    if env_file.exists() and python.exists():
        try:
            result = subprocess.run(
                [str(python), "-c", """
import sys
sys.path.insert(0, '.')
from core.config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT count(*) FROM canonical_properties"))
    count = result.scalar()
    print(f"DB OK: {count} canonical properties")
"""],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT),
                timeout=15,
            )
            if result.returncode == 0:
                print(f"[OK] Database: {result.stdout.strip()}")
            else:
                print(f"[FAIL] Database connection failed:")
                print(f"  {result.stderr.strip()}")
                all_ok = False
        except subprocess.TimeoutExpired:
            print("[FAIL] Database connection timed out")
            all_ok = False
        except Exception as e:
            print(f"[FAIL] Database check error: {e}")
            all_ok = False

    # 5. Data integrity
    if python.exists() and env_file.exists():
        try:
            result = subprocess.run(
                [str(python), "-c", """
import sys; sys.path.insert(0, '.')
from core.database import SessionLocal
from core.models import Source, RawListing, CanonicalProperty, Location, ListingHistory
db = SessionLocal()
try:
    print(f"sources={db.query(Source).count()}")
    print(f"locations={db.query(Location).count()}")
    print(f"raw_listings={db.query(RawListing).count()}")
    print(f"canonical_properties={db.query(CanonicalProperty).count()}")
    print(f"listing_history={db.query(ListingHistory).count()}")
finally:
    db.close()
"""],
                capture_output=True, text=True, cwd=str(PROJECT_ROOT),
                timeout=15,
            )
            if result.returncode == 0:
                print(f"[OK] Data counts: {result.stdout.strip().replace(chr(10), ', ')}")
            else:
                print(f"[WARN] Data count check failed: {result.stderr.strip()}")
        except Exception:
            pass

    print()
    if all_ok:
        print("All checks passed. The API is ready to start.")
    else:
        print("Some checks failed. Fix the issues above before starting the API.")


# ---------------------------------------------------------------------------
# Command: restore
# ---------------------------------------------------------------------------
def cmd_restore(args: argparse.Namespace) -> None:
    """Restore the database from the dump file."""
    print("=== CentralImmo: Database Restore ===\n")

    # We need the DATABASE_URL from .env
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.config import settings

    db_url = settings.database_url
    # Parse DATABASE_URL into components for pg_restore/psql
    # Format: postgresql://user:pass@host:port/dbname
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    db_host = parsed.hostname or "localhost"
    db_port = str(parsed.port or 5432)
    db_user = parsed.username or "immo_user"
    db_pass = parsed.password or ""
    db_name = parsed.path.lstrip("/") or "immo_db"

    # Try custom format first (pg_restore), fall back to plain SQL (psql).
    if DUMP_FILE.exists():
        print(f"[1/2] Restoring from custom dump: {DUMP_FILE}")
        env = {**os.environ, "PGPASSWORD": db_pass}
        try:
            run([
                "pg_restore",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                str(DUMP_FILE),
            ], env=env)
        except subprocess.CalledProcessError:
            print("  -> pg_restore had issues, retrying...")
            run([
                "pg_restore",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                str(DUMP_FILE),
            ], env=env)
    elif SQL_DUMP_FILE.exists():
        print(f"[1/2] Restoring from SQL dump: {SQL_DUMP_FILE}")
        env = {**os.environ, "PGPASSWORD": db_pass}
        run([
            "psql",
            f"--host={db_host}",
            f"--port={db_port}",
            f"--username={db_user}",
            f"--dbname={db_name}",
            "-f", str(SQL_DUMP_FILE),
        ], env=env)
    else:
        print("[ERROR] No database dump found. Expected one of:")
        print(f"  {DUMP_FILE}")
        print(f"  {SQL_DUMP_FILE}")
        sys.exit(1)

    print("\n[2/2] Verifying restore...")
    env = {**os.environ, "PGPASSWORD": db_pass}
    result = subprocess.run([
        "psql",
        f"--host={db_host}",
        f"--port={db_port}",
        f"--username={db_user}",
        f"--dbname={db_name}",
        "-t", "-c",
        "SELECT 'canonical_properties: ' || count(*) FROM canonical_properties;",
    ], env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  -> {result.stdout.strip()}")
    print("\nDatabase restore complete.")


# ---------------------------------------------------------------------------
# Command: migrate
# ---------------------------------------------------------------------------
def cmd_migrate(args: argparse.Namespace) -> None:
    """Run Alembic migrations."""
    print("=== CentralImmo: Database Migrations ===\n")

    python = str(VENV_DIR / "bin" / "python") if (VENV_DIR / "bin" / "python").exists() else sys.executable

    # Check current revision
    print("[1/3] Current migration state:")
    result = subprocess.run(
        [python, "-m", "alembic", "current"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    print(f"  {result.stdout.strip() or result.stderr.strip()}")

    # Run migrations
    print("[2/3] Running migrations...")
    result = subprocess.run(
        [python, "-m", "alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  -> {result.stdout.strip()}")
    else:
        print(f"  [ERROR] {result.stderr.strip()}")
        sys.exit(1)

    # Show new state
    print("[3/3] New migration state:")
    result = subprocess.run(
        [python, "-m", "alembic", "current"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    print(f"  {result.stdout.strip() or result.stderr.strip()}")
    print("\nMigrations complete.")


# ---------------------------------------------------------------------------
# Command: info
# ---------------------------------------------------------------------------
def cmd_info(args: argparse.Namespace) -> None:
    """Print a summary of the current configuration."""
    print("=== CentralImmo: Configuration Summary ===\n")

    print(f"Project root:  {PROJECT_ROOT}")
    print(f"Deploy dir:    {DEPLOY_DIR}")
    print(f"Venv:          {VENV_DIR}")
    print(f"Requirements:  {REQUIREMENTS_FILE} ({'exists' if REQUIREMENTS_FILE.exists() else 'MISSING'})")
    print(f"Dump (custom): {DUMP_FILE} ({'exists' if DUMP_FILE.exists() else 'MISSING'})")
    print(f"Dump (sql):    {SQL_DUMP_FILE} ({'exists' if SQL_DUMP_FILE.exists() else 'MISSING'})")

    env_file = PROJECT_ROOT / ".env"
    print(f"\n.env file:     {env_file} ({'exists' if env_file.exists() else 'MISSING'})")

    if env_file.exists():
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            from core.config import settings
            print(f"\n  DATABASE_URL:  {settings.database_url}")
            print(f"  API_HOST:      {settings.api_host}")
            print(f"  API_PORT:      {settings.api_port}")
            print(f"  CORS_ORIGINS:  {settings.cors_origins}")
            print(f"  LOG_LEVEL:     {settings.log_level}")
            print(f"  DASHSCOPE_KEY: {'configured' if settings.dashscope_api_key else 'not set'}")
        except Exception as e:
            print(f"  [Error reading settings: {e}]")

    # Show installed packages
    python = VENV_DIR / "bin" / "python"
    if python.exists():
        print(f"\nPython: {python}")
        try:
            result = subprocess.run(
                [str(python), "--version"],
                capture_output=True, text=True,
            )
            print(f"  {result.stdout.strip()}")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(
        description="CentralImmo — Python setup and management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py install       Create venv + install all deps
  python setup.py check         Verify everything is ready
  python setup.py restore       Load database dump into PostgreSQL
  python setup.py migrate       Run Alembic migrations
  python setup.py info          Show configuration summary
        """.strip(),
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="Create venv and install Python dependencies")
    sub.add_parser("check", help="Verify environment, database, and configuration")
    sub.add_parser("restore", help="Restore PostgreSQL database from dump")
    sub.add_parser("migrate", help="Run Alembic migrations")
    sub.add_parser("info", help="Show configuration summary")

    args = p.parse_args()

    commands = {
        "install": cmd_install,
        "check": cmd_check,
        "restore": cmd_restore,
        "migrate": cmd_migrate,
        "info": cmd_info,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
