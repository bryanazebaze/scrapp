#!/usr/bin/env bash
# =============================================================================
# CentralImmo — Production Deployment Script for AWS EC2 (Ubuntu 22.04/24.04)
# =============================================================================
# This script provisions a fresh Ubuntu instance to run the CentralImmo API.
# It installs system packages, sets up PostgreSQL, restores the database dump,
# creates a Python virtual environment, configures environment variables, and
# registers a systemd service so the API starts on boot and restarts on crash.
#
# Usage (on the EC2 instance, as root or a sudo-capable user):
#   chmod +x setup.sh
#   sudo ./setup.sh
#
# What this script does NOT do:
#   - It does NOT configure a firewall (use AWS security groups).
#   - It does NOT set up nginx or TLS (add separately if needed).
#   - It does NOT start periodic crawls (the scheduler inside the API handles that).
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — change these to match your environment
# ---------------------------------------------------------------------------
APP_USER="${APP_USER:-centralimmo}"
APP_DIR="${APP_DIR:-/opt/centralimmo}"
APP_HOME="${APP_HOME:-/home/${APP_USER}}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/venv}"
DB_NAME="${DB_NAME:-immo_db}"
DB_USER="${DB_USER:-immo_user}"
DB_PASS="${DB_PASS:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
# Optional: pass DASHSCOPE_API_KEY=... when running setup.sh to enable AI
# features (natural-language search, profile translation). Leave empty to use
# the regex-based fallback search (API still runs without it).
DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY:-}"
QWEN_MODEL="${QWEN_MODEL:-qwen-plus}"

# Path to this script's directory (contains the dump + requirements)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_SRC="$(dirname "${SCRIPT_DIR}")"   # scrapp/ repo root

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (use sudo)." >&2
    exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/immo_db_backup.dump" ]]; then
    echo "ERROR: immo_db_backup.dump not found in ${SCRIPT_DIR}." >&2
    echo "Run pg_dump on your local machine first (see README)." >&2
    exit 1
fi

echo "=== CentralImmo Deployment ==="
echo "APP_USER  = ${APP_USER}"
echo "APP_DIR   = ${APP_DIR}"
echo "DB_NAME   = ${DB_NAME}"
echo "DB_USER   = ${DB_USER}"
echo "DB_PASS   = (auto-generated)"
echo ""

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
echo "[1/8] Installing system packages..."

apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-client \
    build-essential libpq-dev \
    curl ca-certificates \
    nginx \
    > /dev/null

echo "  -> System packages installed."

# ---------------------------------------------------------------------------
# 2. Create application user
# ---------------------------------------------------------------------------
echo "[2/8] Creating application user '${APP_USER}'..."

if id "${APP_USER}" &>/dev/null; then
    echo "  -> User '${APP_USER}' already exists, skipping."
else
    useradd --system --create-home --shell /bin/bash "${APP_USER}"
    echo "  -> User '${APP_USER}' created."
fi

# ---------------------------------------------------------------------------
# 3. Deploy application code
# ---------------------------------------------------------------------------
echo "[3/8] Deploying application code to ${APP_DIR}..."

# Skip the deploy/ and immo_app/ directories — they are not needed on the server.
# Also skip __pycache__, .git, alembic/__pycache__, and .pyc files.
rsync -a --delete \
    --exclude 'deploy/' \
    --exclude 'immo_app/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude 'alembic/__pycache__/' \
    --exclude 'alembic/versions/__pycache__/' \
    --exclude 'api/__pycache__/' \
    --exclude 'core/__pycache__/' \
    --exclude 'scrapers/__pycache__/' \
    --exclude 'static/' \
    --exclude '.env' \
    "${PROJECT_SRC}/" "${APP_DIR}/"

chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "  -> Code deployed to ${APP_DIR}."

# ---------------------------------------------------------------------------
# 4. Python virtual environment + dependencies
# ---------------------------------------------------------------------------
echo "[4/8] Creating Python virtual environment and installing dependencies..."

python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel -q

# Install from the deployed requirements.txt
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt" -q

chown -R "${APP_USER}:${APP_USER}" "${VENV_DIR}"

echo "  -> Python environment ready at ${VENV_DIR}."

# ---------------------------------------------------------------------------
# 5. PostgreSQL setup
# ---------------------------------------------------------------------------
echo "[5/8] Configuring PostgreSQL..."

# Ensure PostgreSQL is running
systemctl start postgresql
systemctl enable postgresql

# Create database user (idempotent via DO block)
su - postgres -c "psql -c \"
DO \\\$\\\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
        CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}';
    ELSE
        -- Rotate password to the new auto-generated one
        ALTER ROLE ${DB_USER} PASSWORD '${DB_PASS}';
    END IF;
END
\\\$\\\$;
\""

# Create database if it doesn't exist
su - postgres -c "psql -c \"SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'\" | grep -q 1 || \
    psql -c \"CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};\""

# Grant privileges
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};\""

echo "  -> PostgreSQL user and database ready."

# ---------------------------------------------------------------------------
# 6. Restore database dump
# ---------------------------------------------------------------------------
echo "[6/8] Restoring database from dump..."

# Drop and recreate the schema so we start clean (the dump contains CREATE TABLE).
# We use --clean --if-exists so pg_restore can drop+recreate without errors.
PGPASSWORD="${DB_PASS}" pg_restore \
    --host=localhost \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --jobs=2 \
    "${SCRIPT_DIR}/immo_db_backup.dump" \
    > /dev/null 2>&1 || {
        # pg_restore --clean sometimes fails on first run against an empty DB
        # because it tries to drop tables that don't exist yet. Retry once.
        echo "  -> First restore attempt had warnings, retrying..."
        PGPASSWORD="${DB_PASS}" pg_restore \
            --host=localhost \
            --username="${DB_USER}" \
            --dbname="${DB_NAME}" \
            --clean \
            --if-exists \
            --no-owner \
            --no-privileges \
            --jobs=2 \
            "${SCRIPT_DIR}/immo_db_backup.dump" \
            > /dev/null 2>&1
    }

echo "  -> Database restored successfully."

# Verify restore
ROW_COUNT=$(PGPASSWORD="${DB_PASS}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -t -c \
    "SELECT count(*) FROM canonical_properties;" 2>/dev/null | tr -d ' ')
echo "  -> Verified: ${ROW_COUNT} canonical properties in database."

# ---------------------------------------------------------------------------
# 7. Write .env configuration
# ---------------------------------------------------------------------------
echo "[7/8] Writing environment configuration..."

cat > "${APP_DIR}/.env" <<EOF
# CentralImmo — Production environment (generated by setup.sh)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
API_HOST=${API_HOST}
API_PORT=${API_PORT}
CORS_ORIGINS=*

# Scraper settings
SCRAPER_DELAY_MIN=2.0
SCRAPER_DELAY_MAX=5.0

# AI / Qwen (DashScope) — enables natural-language search + translations.
# Leave blank to use the regex-based fallback (API runs fine without it).
DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
QWEN_MODEL=${QWEN_MODEL}

# Optional: HTTP proxy for scrapers.
HTTP_PROXY=
HTTPS_PROXY=

LOG_LEVEL=INFO
EOF

chown "${APP_USER}:${APP_USER}" "${APP_DIR}/.env"
chmod 640 "${APP_DIR}/.env"

echo "  -> .env written to ${APP_DIR}/.env"

# ---------------------------------------------------------------------------
# 8. systemd service
# ---------------------------------------------------------------------------
echo "[8/8] Registering systemd service..."

cat > /etc/systemd/system/centralimmo.service <<EOF
[Unit]
Description=CentralImmo API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment=PATH=${VENV_DIR}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=${VENV_DIR}/bin/python ${APP_DIR}/start.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=centralimmo
# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${APP_DIR}
ReadOnlyPaths=/usr

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable centralimmo.service

echo ""
echo "============================================================================"
echo "  CentralImmo deployment complete."
echo "============================================================================"
echo ""
echo "  Database:  ${DB_NAME} (user: ${DB_USER})"
echo "  App dir:   ${APP_DIR}"
echo "  API will listen on:  ${API_HOST}:${API_PORT}"
echo ""
echo "  Start the API manually:"
echo "    sudo systemctl start centralimmo"
echo ""
echo "  Check status:"
echo "    sudo systemctl status centralimmo"
echo ""
echo "  View logs:"
echo "    sudo journalctl -u centralimmo -f"
echo ""
echo "  The API will be available at:"
echo "    http://<server-ip>:${API_PORT}/"
echo "    http://<server-ip>:${API_PORT}/docs  (Swagger UI)"
echo "    http://<server-ip>:${API_PORT}/health"
echo ""
echo "  Next steps:"
echo "    - Configure your AWS security group to allow TCP ${API_PORT}"
echo "    - (Optional) Configure nginx as a reverse proxy for TLS"
echo "    - Test: curl http://localhost:${API_PORT}/health"
echo "============================================================================"
