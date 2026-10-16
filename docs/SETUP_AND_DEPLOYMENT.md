# Clothing E-commerce Backend — Setup & Deployment Guide

This is the complete, standalone guide to running this project in
development and deploying it to production. It covers everything needed to
go from a fresh clone to a live site: prerequisites, local setup, every
environment variable, Docker, three deployment paths (PaaS, Docker-on-VPS,
bare VPS), security checklist, and troubleshooting.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Quick start (TL;DR)](#2-quick-start-tldr)
3. [Local development setup](#3-local-development-setup)
4. [Environment variables reference](#4-environment-variables-reference)
5. [Database: migrations, seeding, admin user](#5-database-migrations-seeding-admin-user)
6. [Running the application](#6-running-the-application)
7. [Running tests](#7-running-tests)
8. [Docker (local development)](#8-docker-local-development)
9. [Production deployment](#9-production-deployment)
   - [9.1 Pre-deployment checklist](#91-pre-deployment-checklist)
   - [9.2 Option A — PaaS (Render / Railway)](#92-option-a--paas-render--railway)
   - [9.3 Option B — Docker on a VPS](#93-option-b--docker-on-a-vps)
   - [9.4 Option C — Bare VPS (Gunicorn + Nginx + systemd)](#94-option-c--bare-vps-gunicorn--nginx--systemd)
   - [9.5 Database and media storage in production](#95-database-and-media-storage-in-production)
10. [Post-deploy verification](#10-post-deploy-verification)
11. [Useful management commands](#11-useful-management-commands)
12. [Troubleshooting](#12-troubleshooting)
13. [Project structure reference](#13-project-structure-reference)

---

## 1. Prerequisites

| Tool | Version | Required for |
|---|---|---|
| Python | 3.12+ | Running Django |
| PostgreSQL | 16 | The only supported database — this project refuses to start on SQLite |
| pip / venv | any current | Python dependency management |
| Node.js | 20+ (22 recommended) | Building/running the React storefront (`frontend/`) |
| Docker + Docker Compose | optional | Containerized dev/deploy (builds the frontend for you) |
| Redis | optional in dev, required in prod | Celery broker + cache |
| Git | any | Cloning / version control |

This project **will not boot against SQLite or any non-PostgreSQL engine** —
that check is enforced in `config/settings/base.py`.

---

## 2. Quick start (TL;DR)

```bash
# 1. Virtual environment + dependencies
python3 -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt

# 2. Database
sudo -u postgres psql -c "CREATE ROLE shop WITH LOGIN PASSWORD 'change-me' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE clothing_shop OWNER shop;"

# 3. Environment
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
# paste the output into SECRET_KEY= in .env

# 4. Migrate + seed + admin user
python manage.py migrate
python manage.py seed_roles
python manage.py seed_catalog
python manage.py createsuperuser

# 5. Build the React storefront (once)
(cd frontend && npm install && npm run build)

# 6. Run
python manage.py runserver
```

Then open:
- Storefront: http://localhost:8000/
- Admin: http://localhost:8000/admin/
- API docs: http://localhost:8000/api/v1/docs/

---

## 3. Local development setup

### 3.1 Clone and create a virtual environment

```bash
git clone <your-repo-url> clothing-shop-backend
cd clothing-shop-backend
python3 -m venv venv
source venv/bin/activate          # Windows (PowerShell): venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements/dev.txt
```

`requirements/dev.txt` includes everything in `requirements/base.txt` (Django,
DRF, SimpleJWT, PostgreSQL driver, Celery, etc.) plus testing/linting tools
(pytest, factory-boy, ruff). For a production install only, use
`requirements/prod.txt` instead (adds Gunicorn, skips dev tools).

### 3.2 PostgreSQL setup

**Linux / macOS**, assuming PostgreSQL is already installed and running:

```bash
sudo -u postgres psql -c "CREATE ROLE shop WITH LOGIN PASSWORD 'change-me' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE clothing_shop OWNER shop;"
```

**Windows:**

1. Download and install PostgreSQL 16 from
   https://www.postgresql.org/download/windows/ (the installer bundles
   pgAdmin and the `psql` command-line tool, and sets up the server as an
   auto-starting Windows service).
2. Open **SQL Shell (psql)** from the Start menu. Press Enter to accept each
   default prompt (server/port/database/username) until asked for a
   password — enter the `postgres` superuser password you set during
   install.
3. Run:
   ```sql
   CREATE ROLE shop WITH LOGIN PASSWORD 'change-me' CREATEDB;
   CREATE DATABASE clothing_shop OWNER shop;
   ```
4. Confirm the service is running: **Start → Services → `postgresql-x64-16`
   → Status: Running**.
5. In `.env`, use `DB_HOST=localhost` and `DB_PORT=5432` (the installer's
   defaults).

**macOS with Homebrew**, as an alternative to a manual install:

```bash
brew install postgresql@16
brew services start postgresql@16
createuser -s shop
psql -c "ALTER ROLE shop WITH PASSWORD 'change-me';"
createdb -O shop clothing_shop
```

### 3.3 Environment variables

```bash
cp .env.example .env
```

Generate a real secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Paste the result into `SECRET_KEY=` in `.env`. At minimum for local dev, also
set `DB_USER`, `DB_PASSWORD`, `DB_NAME` to match what you created in step
3.2. See [section 4](#4-environment-variables-reference) for the full list.

**Never commit `.env`.** It's already in `.gitignore`; `.env.example` is the
template that *is* committed (with no real secrets in it).

### 3.4 Apply migrations

```bash
python manage.py migrate
```

This creates every table across all apps (`accounts`, `catalog`, `cart`,
`customers`, `orders`, plus Django/DRF/axes internals). You should see a list
of `Applying <app>.<migration>... OK` lines with no errors.

---

## 4. Environment variables reference

All of these live in `.env` (copied from `.env.example`). Variables not set
fall back to the defaults shown.

### Core

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | *(none — required)* | Generate with the command above. In production, must be ≥50 chars and not start with `django-insecure`, or the app refuses to boot. |
| `DEBUG` | `False` | Set `True` only for local development. Production refuses to boot if `True`. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` (dev adds `testserver`, `[::1]`) | Comma-separated. Production refuses `*`. |
| `ADMIN_URL` | `admin/` | Change this in production to obscure the admin login path (e.g. `secret-staff-login/`). |
| `FRONTEND_URL` | `http://localhost:5173` | Used to build password-reset links (`<FRONTEND_URL>/reset-password?uid=…&token=…`). Set to your public site URL in production. |

### Database

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | *(unset)* | If set, overrides all `DB_*` fields below (e.g. `postgres://user:pass@host:5432/dbname`). |
| `DB_NAME` | `clothing_shop` | |
| `DB_USER` | `postgres` | |
| `DB_PASSWORD` | *(empty)* | |
| `DB_HOST` | `localhost` | |
| `DB_PORT` | `5432` | |
| `DB_CONN_MAX_AGE` | `60` | Seconds a DB connection is reused for. |

### Redis / Celery

| Variable | Default | Notes |
|---|---|---|
| `REDIS_URL` | *(unset — falls back to in-memory cache)* | e.g. `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | same as `REDIS_URL` | |
| `CELERY_TASK_ALWAYS_EAGER` | `True` in dev, `False` elsewhere | When `True`, Celery tasks run synchronously in-process — no worker needed. |

### CORS / CSRF

| Variable | Default | Notes |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | dev: localhost:3000/5173/5500/8080 | Comma-separated full origins (scheme + host + port). Production **requires** this to be set. |
| `CORS_ALLOW_CREDENTIALS` | `False` | |
| `CSRF_TRUSTED_ORIGINS` | *(empty)* | Needed if you serve a frontend that submits CSRF-protected requests cross-origin. |

### JWT / brute-force protection

| Variable | Default | Notes |
|---|---|---|
| `JWT_ACCESS_MINUTES` | `15` | |
| `JWT_REFRESH_DAYS` | `7` | |
| `AXES_ENABLED` | `True` | Locks out repeated failed logins. |
| `AXES_FAILURE_LIMIT` | `5` | |
| `AXES_COOLOFF_MINUTES` | `15` | |

### Email (password reset)

| Variable | Default | Notes |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Dev default — prints emails to the terminal. Set to `...backends.smtp.EmailBackend` in production. |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | — | Standard SMTP settings. |
| `DEFAULT_FROM_EMAIL` | `Shop <no-reply@example.com>` | |

### Shop

| Variable | Default | Notes |
|---|---|---|
| `DELIVERY_CHARGE_INSIDE_DHAKA` | `60` | Flat delivery charge applied at checkout when the shipping city is Dhaka. |
| `DELIVERY_CHARGE_OUTSIDE_DHAKA` | `120` | Applied for any other city. |

### Cloud storage (optional — for production media)

| Variable | Notes |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_STORAGE_BUCKET_NAME` / `AWS_S3_REGION_NAME` | Only needed once you switch `STORAGES["default"]` to `django-storages` for S3-backed media (see [9.5](#95-database-and-media-storage-in-production)). |

### Misc

| Variable | Default | Notes |
|---|---|---|
| `LOG_LEVEL` | `INFO` | |
| `API_DOCS_PUBLIC` | `True` | If `False`, Swagger/ReDoc require admin auth to view. |
| `SECURE_SSL_REDIRECT` | `True` (prod only) | Forces HTTPS. |
| `SECURE_HSTS_SECONDS` | `31536000` (prod only) | |

---

## 5. Database: migrations, seeding, admin user

```bash
# Apply all migrations (run this after every pull that touches models/)
python manage.py migrate

# Create baseline staff permission groups (Catalog Manager, Order Manager, etc.)
python manage.py seed_roles

# Populate demo categories/products/variants with real stock, so the
# storefront isn't empty. Safe to re-run — it skips existing rows.
python manage.py seed_catalog

# Create your own admin login
python manage.py createsuperuser
```

`createsuperuser` will prompt for email, phone (optional — press Enter to
skip), and password. Use that login at `/admin/`.

---

## 6. Running the application

```bash
python manage.py runserver
```

This single command serves **everything** (build the frontend first — see
[6.1](#61-the-react-storefront)):

| What | URL |
|---|---|
| Storefront (shop/cart/checkout/orders UI) | http://localhost:8000/ |
| Django Admin | http://localhost:8000/admin/ |
| REST API root | http://localhost:8000/api/v1/ |
| Health check | http://localhost:8000/api/v1/health/ |
| Swagger UI | http://localhost:8000/api/v1/docs/ |
| ReDoc | http://localhost:8000/api/v1/redoc/ |
| Raw OpenAPI schema | http://localhost:8000/api/v1/schema/ |

The storefront and the API are same-origin (Django serves both), so no CORS
configuration is needed to use the bundled storefront locally.

### 6.1 The React storefront

The customer website lives in `frontend/` (React 19 + Vite + React Router).
Django serves its production build, so there are two ways to work with it:

```bash
# A) Production-style: build once, Django serves it at http://localhost:8000/
cd frontend
npm install
npm run build          # re-run after frontend changes

# B) Development: hot reload at http://localhost:5173 (proxies /api, /media,
#    /admin to Django on :8000 — keep `python manage.py runserver` running)
cd frontend
npm run dev
```

Optional build-time settings go in `frontend/.env.local` (see
`frontend/.env.example`): `VITE_SHOP_NAME` (brand name), `VITE_API_BASE` (only
if the API is on another origin). If `/` shows "The React storefront hasn't
been built yet", run option A.

Frontend tests: `cd frontend && npm test` (unit, no server needed) and
`E2E=1 npm test` (adds the full browsing→checkout journey; needs the backend
running with `seed_catalog` data).

To run Celery for real (only needed once you add tasks that shouldn't block
a request — this project runs tasks synchronously by default in dev):

```bash
# requires REDIS_URL set and CELERY_TASK_ALWAYS_EAGER=False in .env
celery -A config worker -l info
celery -A config beat -l info      # if/when scheduled tasks exist
```

---

## 7. Running tests

```bash
pytest                    # full suite
pytest -v                  # verbose, one line per test
pytest apps/orders           # just one app
pytest -k "checkout"          # by keyword
pytest -m concurrency          # just the real multi-threaded stock-locking test
```

Tests run against real PostgreSQL (Django's standard throwaway
`test_<DB_NAME>` database, created and destroyed automatically — never
SQLite) and use a fast MD5 password hasher for speed (production always uses
Argon2; this is asserted by a dedicated test so the two can't drift).

Also useful before committing:

```bash
ruff check apps config manage.py     # lint
ruff format apps config manage.py     # auto-format
python manage.py check                 # Django system checks
python manage.py spectacular --fail-on-warn --file /tmp/schema.yaml   # OpenAPI schema validity
```

---

## 8. Docker (local development)

```bash
cp .env.example .env     # fill in a real SECRET_KEY at minimum
docker compose up --build
```

The image build includes a Node stage that compiles the React app, so no local
Node install is needed for Docker. This starts five services:

| Service | What it runs |
|---|---|
| `db` | PostgreSQL 16 |
| `redis` | Redis (cache + Celery broker) |
| `web` | Gunicorn — runs `migrate` and `collectstatic` automatically on boot |
| `worker` | Celery worker |
| `beat` | Celery beat scheduler |

Seed demo data inside the running container:

```bash
docker compose exec web python manage.py seed_catalog
docker compose exec web python manage.py createsuperuser
```

Then visit the same URLs as [section 6](#6-running-the-application), just on
whatever port you've mapped (default `8000`).

To stop: `docker compose down` (add `-v` to also delete the Postgres volume
and start fresh next time).

---

## 9. Production deployment

### 9.1 Pre-deployment checklist

Before deploying anywhere:

- [ ] `SECRET_KEY` is a real, random, ≥50-character value — **not** the one from your `.env.example` or dev `.env`
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` lists your real domain(s) — not `*`
- [ ] `CORS_ALLOWED_ORIGINS` lists your real frontend origin(s)
- [ ] `DJANGO_SETTINGS_MODULE=config.settings.prod`
- [ ] A managed PostgreSQL instance is provisioned and `DATABASE_URL` (or `DB_*`) points to it
- [ ] A managed Redis instance is provisioned if you're using Celery in production
- [ ] Email is configured with a real SMTP backend (not the console backend) if password reset needs to actually deliver
- [ ] You've decided on a media storage strategy (see [9.5](#95-database-and-media-storage-in-production)) if you'll upload product images in production
- [ ] You've run `python manage.py check --deploy` against your real production `.env` and resolved everything except deliberately-skipped items (this project ships passing with only the optional HSTS-preload warning left for you to opt into)
- [ ] `frontend/dist` exists in the deployed artifact (Docker builds it automatically; on a bare VPS/PaaS without Docker run `cd frontend && npm ci && npm run build` as part of the build step)
- [ ] `FRONTEND_URL` is your public site URL so password-reset emails link to the right place

`config/settings/prod.py` **enforces several of these automatically** — the
app will refuse to start (raising `ImproperlyConfigured`) if `DEBUG=True`,
`SECRET_KEY` looks unsafe, `ALLOWED_HOSTS` is empty or `*`, or
`CORS_ALLOWED_ORIGINS` is empty.

---

### 9.2 Option A — PaaS (Render / Railway)

These platforms build from your Dockerfile or detect Python automatically.
Steps are nearly identical on both:

1. **Push your code** to a Git repository the platform can access.
2. **Create a PostgreSQL database** from the platform's dashboard — it will
   give you a `DATABASE_URL`.
3. **Create a Redis instance** (optional, only if using Celery) — gives you
   a `REDIS_URL`.
4. **Create a new Web Service**, pointing at your repo:
   - If using the Dockerfile: the platform auto-detects it, no extra config needed.
   - If not using Docker: set the build command to
     `pip install -r requirements/prod.txt && (cd frontend && npm ci && npm run build)` (the platform needs Node available at build time — or just use the Dockerfile route above) and the start command to
     `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn -c gunicorn.conf.py config.wsgi:application`.
5. **Set environment variables** in the platform's dashboard (not in a
   committed file): every variable from [section 4](#4-environment-variables-reference),
   plus:
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`
   - `DATABASE_URL` → paste the value the platform gave you in step 2
   - `REDIS_URL` → from step 3, if applicable
   - `ALLOWED_HOSTS` → your service's domain (e.g. `myshop.onrender.com`)
   - `CORS_ALLOWED_ORIGINS` → your frontend's real origin
6. **Set the health check path** to `/api/v1/health/` if the platform asks for one.
7. **Deploy.** Watch the build/deploy logs for the `migrate` and
   `collectstatic` steps completing successfully.
8. Once live, run the seed/superuser commands via the platform's shell/console feature:
   ```bash
   python manage.py seed_catalog
   python manage.py createsuperuser
   ```

---

### 9.3 Option B — Docker on a VPS

On any VPS (DigitalOcean Droplet, AWS EC2, Linode, etc.) with Docker and
Docker Compose installed:

```bash
# On the server
git clone <your-repo-url> clothing-shop-backend
cd clothing-shop-backend
cp .env.example .env
nano .env   # fill in real production values per section 4 + the checklist in 9.1

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# One-time setup
docker compose exec web python manage.py seed_catalog
docker compose exec web python manage.py createsuperuser
```

Put a reverse proxy (Nginx or Caddy) in front of the `web` container to
terminate TLS and forward to port 8000. A minimal Nginx example:

```nginx
server {
    listen 80;
    server_name myshop.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name myshop.example.com;

    ssl_certificate     /etc/letsencrypt/live/myshop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myshop.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Use [Certbot](https://certbot.eff.org/) for free Let's Encrypt certificates.
`SECURE_PROXY_SSL_HEADER` is already configured in `config/settings/prod.py`
to trust the `X-Forwarded-Proto` header from a reverse proxy like this.

---

### 9.4 Option C — Bare VPS (Gunicorn + Nginx + systemd, no Docker)

```bash
# On the server (Ubuntu example)
sudo apt update
sudo apt install python3.12 python3.12-venv postgresql nginx -y

git clone <your-repo-url> /opt/clothing-shop-backend
cd /opt/clothing-shop-backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements/prod.txt
(cd frontend && npm ci && npm run build)    # needs Node 20+ on the server

cp .env.example .env
nano .env   # fill in real production values

# Database (same as local setup, section 3.2)
sudo -u postgres psql -c "CREATE ROLE shop WITH LOGIN PASSWORD 'strong-password-here' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE clothing_shop OWNER shop;"

export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_catalog
python manage.py createsuperuser
```

Create a systemd service so Gunicorn runs persistently and restarts on
failure/reboot — `/etc/systemd/system/clothing-shop.service`:

```ini
[Unit]
Description=Clothing Shop Gunicorn
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/clothing-shop-backend
Environment="DJANGO_SETTINGS_MODULE=config.settings.prod"
EnvironmentFile=/opt/clothing-shop-backend/.env
ExecStart=/opt/clothing-shop-backend/venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now clothing-shop
sudo systemctl status clothing-shop
```

Then configure Nginx as a reverse proxy exactly as shown in
[9.3](#93-option-b--docker-on-a-vps), and set up Celery worker/beat as their
own systemd services (same pattern, different `ExecStart`:
`celery -A config worker -l info`) if you need them.

To deploy an update:
```bash
cd /opt/clothing-shop-backend
git pull
source venv/bin/activate
pip install -r requirements/prod.txt
(cd frontend && npm ci && npm run build)
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart clothing-shop
```

---

### 9.5 Database and media storage in production

- **Database:** use a managed PostgreSQL instance (Render/Railway/DigitalOcean/
  AWS RDS all offer one) rather than self-hosting on the same box as the app,
  for backups and reliability. Point `DATABASE_URL` at it.
- **Media (uploaded product images):** by default this project stores
  uploads on local disk (`MEDIA_ROOT`). On most PaaS platforms, **local disk
  does not persist across deploys or restarts** — any images uploaded via
  Django Admin will vanish on the next deploy. Before relying on image
  uploads in production:
  1. Provision an S3-compatible bucket (AWS S3, Cloudflare R2, DigitalOcean
     Spaces, or Cloudinary).
  2. Set the `AWS_*` variables in `.env` (already listed in
     `.env.example`).
  3. In `config/settings/prod.py`, change:
     ```python
     STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
     ```
  `django-storages` is already a dependency, so no new packages are needed —
  this is a settings change only.

---

## 10. Post-deploy verification

After any deployment, confirm:

```bash
curl https://your-domain.com/api/v1/health/
# expect: {"success": true, "message": "Success.", "data": {"status": "ok", "database": true}}
```

Then manually check:
- [ ] Storefront loads at `/`
- [ ] You can register a new account and log in
- [ ] Products appear (run `seed_catalog` if not)
- [ ] You can add to cart and complete a checkout
- [ ] `/admin/` logs in with your superuser and shows Products/Orders
- [ ] `/api/v1/docs/` loads the Swagger UI

---

## 11. Useful management commands

| Command | Purpose |
|---|---|
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Generate new migrations after model changes |
| `python manage.py createsuperuser` | Create a Django Admin login |
| `python manage.py seed_roles` | Create baseline staff permission groups |
| `python manage.py seed_catalog` | Seed demo categories/products/variants (idempotent) |
| `python manage.py collectstatic --noinput` | Gather static files for production serving |
| `python manage.py check` | Django system checks |
| `python manage.py check --deploy` | Production-readiness security checks |
| `python manage.py spectacular --file schema.yaml` | Export the OpenAPI schema |
| `python manage.py shell` | Interactive Python shell with Django loaded |
| `python manage.py dbshell` | Interactive `psql` shell using the project's DB config |

---

## 12. Troubleshooting

**`django.core.exceptions.ImproperlyConfigured: This project requires PostgreSQL`**
→ Your `DATABASE_URL`/`DB_*` settings are pointing at something other than
PostgreSQL, or PostgreSQL isn't running. Check `DB_HOST`/`DB_PORT` and that
the database server is actually up (`pg_isready` or `sudo systemctl status postgresql`).

**`django.core.exceptions.ImproperlyConfigured: SECRET_KEY is not set`**
→ You haven't copied `.env.example` to `.env`, or didn't fill in
`SECRET_KEY`. Run the generator command from [section 3.3](#33-environment-variables).

**Production refuses to start with "DEBUG must be False" / "SECRET_KEY must be strong" / "ALLOWED_HOSTS must list..."**
→ These are intentional fail-fast checks in `config/settings/prod.py`. Fix
the underlying `.env` value — don't bypass them.

**CORS errors in the browser console when using a separate frontend**
→ Add that frontend's exact origin (scheme + host + port) to
`CORS_ALLOWED_ORIGINS` in `.env` and restart the server. If you're using the
React app served by Django at `/` (or `npm run dev`, which proxies the API),
this shouldn't happen — both are same-origin by design. You only need CORS if
you host the frontend on a different domain than the API (set `VITE_API_BASE`
at build time and add that origin here).

**`relation "..." does not exist` errors**
→ Migrations haven't been applied. Run `python manage.py migrate`.

**Checkout returns 400 "The Idempotency-Key header is required"**
→ By design — every checkout request must include an `Idempotency-Key`
header (any unique string per checkout attempt) so retried requests don't
create duplicate orders.

**Product images missing after a redeploy (PaaS)**
→ See [9.5](#95-database-and-media-storage-in-production) — local disk
storage isn't persistent on most platforms; switch to S3-compatible storage.

**Locked out of login during local testing**
→ django-axes locks an IP+identifier combo after repeated failed attempts
(`AXES_FAILURE_LIMIT`, default 5). Wait out `AXES_COOLOFF_MINUTES`, or in
dev, clear it: `python manage.py axes_reset`.

---

## 13. Project structure reference

```
clothing-shop-backend/
├── manage.py
├── gunicorn.conf.py
├── Dockerfile  docker-compose.yml  docker-compose.prod.yml
├── requirements/{base,dev,prod}.txt
├── pytest.ini  conftest.py  pyproject.toml
├── .env.example
├── frontend/                 # React storefront (Vite)
│   ├── src/{pages,components,context,lib,test}
│   └── dist/                 # production build, served by Django at "/"
├── config/
│   ├── settings/{base,dev,test,prod}.py
│   ├── urls.py                # mounts admin, API, docs, React app (SPA fallback)
│   ├── api_v1.py               # mounts every app's routes under /api/v1/
│   └── celery.py  wsgi.py  asgi.py
└── apps/
    ├── core/          # shared: envelope renderer, pagination, exceptions,
    │                  # permissions, throttles, logging, idempotency, health
    ├── accounts/      # custom User, JWT auth, registration/login/password
    ├── catalog/       # categories, products, variants, filtering, admin
    ├── cart/          # cart + items, server-side pricing
    ├── customers/     # saved addresses
    ├── orders/        # checkout service, order state machine, admin
    └── */tests/       # every app has its own test suite
```

For the full feature list, API endpoint table, and security notes, see
`README.md` in the project root.
