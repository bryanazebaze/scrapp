#!/usr/bin/env python3
"""CentralImmo API — production server entry point + daemon controller.

Runs the FastAPI backend (main_api:app) via uvicorn. Reads configuration from
.env in the same directory (via core.config.settings), so the same file that
deploy/setup.sh generates drives host/port/cors.

Modes:
    python start.py                   # foreground (default; used by systemd)
    python start.py daemon            # detached background daemon (PID file)
    python start.py stop              # stop the daemon
    python start.py restart           # stop + daemon
    python start.py status            # show running state

Foreground flags (also accepted in daemon mode):
    --host <addr>    override API_HOST   (default: from .env)
    --port <port>    override API_PORT   (default: from .env)
    --workers <n>    uvicorn workers     (default: 1; 0 = auto)
    --log-level <l>  debug|info|warning|error|critical

Daemon mode writes logs/api.log and a PID file at run/centralimmo.pid.

The API exposes:
  /  /docs  /health  /annonces  /search  /neighborhoods  /profiles  /admin
"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path so `from core...` works regardless
# of where the process is started from.
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uvicorn  # noqa: E402
from core.config import settings  # noqa: E402

ROOT = Path(_project_root)
LOG_DIR = ROOT / "logs"
PID_FILE = ROOT / "run" / "centralimmo.pid"
LOG_FILE = LOG_DIR / "api.log"

DAEMON_COMMANDS = {"daemon", "stop", "restart", "status"}


def _ensure_dirs():
    LOG_DIR.mkdir(exist_ok=True)
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)


def _read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _clear_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def _build_foreground_argv(args: argparse.Namespace) -> list[str]:
    """Reconstruct the argv used to (re)launch in foreground mode."""
    return [
        sys.executable, str(ROOT / "start.py"), "foreground",
        "--host", str(args.host),
        "--port", str(args.port),
        "--workers", str(args.workers),
        "--log-level", str(args.log_level),
    ]


def run_foreground(args: argparse.Namespace) -> None:
    """Run uvicorn in the foreground (blocks). Used by systemd."""
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("centralimmo")
    logger.info("Starting CentralImmo API v3 on %s:%s (workers=%s)",
                args.host, args.port, args.workers)
    redacted = settings.database_url
    if "://" in redacted and "@" in redacted:
        creds = redacted.split("://", 1)[1].split("@", 1)[0]
        redacted = redacted.replace(creds, "***")
    logger.info("Database: %s", redacted)

    workers = args.workers if args.workers > 0 else None
    uvicorn.run(
        "main_api:app",
        host=args.host,
        port=args.port,
        workers=workers,
        log_level=args.log_level,
        proxy_headers=True,        # trust X-Forwarded-* behind nginx
        forwarded_allow_ips="*",   # safe behind AWS SG + nginx
        access_log=(args.log_level == "debug"),
    )


def start_daemon(args: argparse.Namespace) -> None:
    """Launch uvicorn detached (subprocess + new session). PID file + log file."""
    _ensure_dirs()
    pid = _read_pid()
    if pid and _alive(pid):
        print(f"Already running (PID {pid}). Use 'restart' to reload.")
        sys.exit(0)

    log_fp = open(LOG_FILE, "ab", buffering=0)
    proc = subprocess.Popen(
        _build_foreground_argv(args),
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,   # detach: survives the launching shell
        cwd=str(ROOT),
    )
    PID_FILE.write_text(str(proc.pid))
    time.sleep(1.5)
    if proc.poll() is None:
        print(f"CentralImmo API started (PID {proc.pid})")
        print(f"  listening on {args.host}:{args.port}")
        print(f"  logs: {LOG_FILE}")
    else:
        print(f"Process exited immediately (code {proc.returncode}). See {LOG_FILE}.")
        _clear_pid()
        sys.exit(1)


def stop_daemon() -> None:
    pid = _read_pid()
    if not pid:
        print("Not running (no PID file).")
        return
    if not _alive(pid):
        print(f"Stale PID file for {pid}; cleaning up.")
        _clear_pid()
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except PermissionError:
        print(f"Cannot signal PID {pid} (permission denied).")
        sys.exit(1)
    for _ in range(20):
        if not _alive(pid):
            break
        time.sleep(0.25)
    if _alive(pid):
        print(f"Graceful stop timed out; sending SIGKILL to {pid}.")
        os.kill(pid, signal.SIGKILL)
    _clear_pid()
    print(f"Stopped (PID {pid}).")


def status() -> None:
    pid = _read_pid()
    if pid and _alive(pid):
        print(f"Running (PID {pid}) on {settings.api_host}:{settings.api_port}")
    else:
        print("Not running.")
        if pid:
            _clear_pid()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CentralImmo API server + daemon controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("command", nargs="?", default="foreground",
                   choices=["foreground", "daemon", "stop", "restart", "status"],
                   help="daemon control (default: foreground)")
    p.add_argument("--host", default=settings.api_host,
                   help=f"bind address (default: {settings.api_host})")
    p.add_argument("--port", type=int, default=settings.api_port,
                   help=f"bind port (default: {settings.api_port})")
    p.add_argument("--workers", type=int, default=1,
                   help="uvicorn workers (default: 1; 0 = auto)")
    p.add_argument("--log-level", default=settings.log_level.lower(),
                   choices=("debug", "info", "warning", "error", "critical"),
                   help=f"log level (default: {settings.log_level.lower()})")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "foreground":
        run_foreground(args)
    elif args.command == "daemon":
        start_daemon(args)
    elif args.command == "stop":
        stop_daemon()
    elif args.command == "restart":
        stop_daemon()
        time.sleep(1)
        start_daemon(args)
    elif args.command == "status":
        status()


if __name__ == "__main__":
    main()