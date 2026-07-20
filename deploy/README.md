# CentralImmo — Backend Deployment (AWS EC2, Ubuntu)

This guide deploys the **FastAPI backend** with the **current database snapshot**
so the Flutter frontend can hit the API immediately — no re-scraping required.

## What's in this directory

| File | Purpose |
|---|---|
| `setup.sh` | One-shot server provisioning (system pkgs, Postgres, venv, DB restore, systemd) |
| `start.py` *(repo root)* | API launcher: `foreground` (systemd) / `daemon` / `stop` / `restart` / `status` |
| `immo_db_backup.dump` | Full pg_dump of `immo_db` (schema + data, post-migration `0005_bilingual`) |
| `README.md` | This file |

The dump includes all 12 tables (sources, raw_listings, canonical_properties,
locations, listing_history, neighborhood_analytics, city_profiles,
neighborhood_profiles, listing_translations, image_cache, scheduler_jobs,
alembic_version) — 222 listings, 198 canonical properties, 86 neighborhood
profiles, 10 city profiles, 221 English translations, etc.

---

## Step 1 — On your local machine: export the DB (only if data changed)

The committed `deploy/immo_db_backup.dump` is current as of the last export.
Re-export whenever the local DB changes:

```bash
cd scrapp
PGPASSWORD=1234 pg_dump -h localhost -U immo_user -d immo_db \
    -Fc --no-owner --no-acl -f deploy/immo_db_backup.dump
git add deploy/immo_db_backup.dump
git commit -m "Refresh DB dump for deployment"
git push
```

## Step 2 — Launch the EC2 instance

- AMI: **Ubuntu Server 22.04 LTS or 24.04 LTS** (x86_64, `t3.micro` is enough
  for this dataset; scale up if you add crawlers/traffic).
- Storage: 8 GB gp3 is plenty.
- **Security group:** open inbound **TCP 8000** (API) and **TCP 22** (SSH).
  Restrict 22 to your IP. For production, put nginx on 443 and keep 8000
  private — see "Hardening" below.
- SSH key: save the `.pem`.

## Step 3 — On the server: pull the repo and run setup

```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/<you>/scrapp.git /tmp/scrapp
cd /tmp/scrapp

# Optional: enable AI features (NL search + translations) by passing the key
sudo QWEN_API_KEY=sk-xxxx ./deploy/setup.sh
#   — or without AI features —
sudo ./deploy/setup.sh
```

`setup.sh` will:
1. Install Python 3, PostgreSQL, build tools, nginx.
2. Create a system user `centralimmo` and deploy code to `/opt/centralimmo`.
3. Create a Python venv and `pip install -r requirements.txt`.
4. Create the `immo_user` Postgres role (auto-generated password) + `immo_db`.
5. Restore `deploy/immo_db_backup.dump` into `immo_db`.
6. Generate `/opt/centralimmo/.env` (DB URL, `API_HOST=0.0.0.0`, CORS, Qwen key).
7. Register + enable the `centralimmo` systemd service.

At the end it prints the generated DB password — **save it** (it's also in
`/opt/centralimmo/.env`).

## Step 4 — Start & verify

```bash
sudo systemctl start centralimmo
sudo systemctl status centralimmo
curl http://localhost:8000/health
```

Expected: `{"status":"ok","version":"3.0.0","database":"connected","scheduler_running":true}`

From your laptop:
```bash
curl http://<EC2-PUBLIC-IP>:8000/health
curl "http://<EC2-PUBLIC-IP>:8000/annonces?limit=3"
```

Point the Flutter app at it:
```bash
flutter run --dart-define=API_BASE_URL=http://<EC2-PUBLIC-IP>:8000
```

## Step 5 — Managing the service

```bash
sudo systemctl start|stop|restart|status centralimmo
sudo journalctl -u centralimmo -f          # live logs
```

Manual daemon mode (without systemd) — useful for debugging:
```bash
cd /opt/centralimmo
source venv/bin/activate
python start.py daemon      # background
python start.py status
python start.py stop
python start.py foreground  # blocks; Ctrl-C to stop
```

---

## Hardening (recommended for production)

1. **TLS via nginx** — don't expose 8000 directly. Put nginx on 443 with
   Let's Encrypt, proxy to `127.0.0.1:8000`. Then close 8000 in the security
   group. setup.sh already installs nginx; add a server block:
   ```nginx
   server {
       server_name api.yourdomain.com;
       location / { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
   }
   ```
2. **Restrict CORS** — edit `/opt/centralimmo/.env`:
   `CORS_ORIGINS=https://app.yourdomain.com` and restart.
3. **Rotate the DB password** — change `DB_PASS` in `.env` and
   `ALTER ROLE immo_user PASSWORD '...';` in psql, then restart.
4. **Backups** — nightly `pg_dump -Fc` to S3.

## Updating the deployment

After pushing new code or a refreshed dump:
```bash
cd /tmp/scrapp && git pull
sudo ./deploy/setup.sh        # re-runs idempotently; restores the latest dump
sudo systemctl restart centralimmo
```

`setup.sh` is idempotent — safe to re-run. The DB restore uses
`pg_restore --clean --if-exists` so existing tables are replaced cleanly.

## Troubleshooting

- **`pg_restore` errors on first run** — setup.sh auto-retries once; this is
  expected against a non-empty DB.
- **API unreachable from outside** — check the AWS security group allows
  TCP 8000 from your IP; check `sudo systemctl status centralimmo`.
- **`alembic_version` mismatch** — the dump already stamps `0005_bilingual`.
  Verify: `PGPASSWORD=... psql -U immo_user -d immo_db -c "SELECT * FROM alembic_version;"`
- **AI features silent** — `QWEN_API_KEY` is empty in `.env`. Re-run
  `sudo QWEN_API_KEY=sk-xxxx ./deploy/setup.sh`.