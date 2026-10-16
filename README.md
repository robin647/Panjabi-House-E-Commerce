# Clothing / Panjabi E-commerce Backend

A production-oriented Django REST Framework backend for a clothing
e-commerce business, with a responsive **React storefront** (in `frontend/`) and a
fully configured Django Admin as its admin UI.

## Status

**Core shopping flow is complete and runnable end-to-end:** browse products,
add to cart, save an address, check out with Cash on Delivery, and view
order history — all backed by real PostgreSQL transactions that prevent
overselling under concurrency. Every piece below was actually exercised
against a live server while building it (real HTTP requests, the real React app
rendered in jsdom against the live API, and multi-threaded concurrency tests),
not just written and assumed correct. One honest caveat: there was no real
browser in the build environment, so the visual design/responsiveness was
verified structurally (every CSS class used exists, mobile-first breakpoints)
but not eyeballed on real devices — give it a look on a phone and a desktop.

**Not yet included** (still on the original roadmap): online payment
gateways beyond COD, coupons, wishlist, product reviews, notifications
(email/SMS beyond password reset), and admin reporting/dashboard endpoints.
The "Admin UI" for this stage is Django Admin — configured properly
(inline variants, order status workflow, search/filters), not a placeholder
— rather than a separate custom React dashboard.

## What's in here

**Customer-facing (REST API + React storefront):**
- Register / login (email or phone) / logout / change / forgot / reset password
- Browse categories and products, filter by category/price, search, sort
- Product detail with size/color variants and live stock
- Cart: add / update / remove, server-computed pricing (client-sent prices are never trusted)
- Saved addresses with a default address
- Checkout (Cash on Delivery): idempotent (safe to retry), stock-locked
  against overselling, snapshots order data so history survives later price
  or product changes
- Order history and order detail

**Admin-facing (Django Admin at `/admin/`):**
- Products with inline variant management (size/color/stock/SKU per variant)
- Categories, product variants (with autocomplete)
- Orders with inline line items, inline status history, and a guarded status
  workflow (state-machine validated transitions, e.g. you can't jump straight
  from Pending to Delivered)
- Customer addresses, users

**Platform:**
- Custom `User` model (email **or** phone login, UUID public identifiers, role field)
- JWT auth via SimpleJWT, role scaffolding, layered permissions
- Brute-force protection (django-axes), per-endpoint throttling
- Consistent JSON envelope on every response, no stack traces ever leaked
- OpenAPI 3 schema (Swagger + ReDoc) — zero schema generation warnings, all 20 endpoints documented
- Structured logging with secret redaction and per-request correlation IDs
- Docker + docker-compose (web, worker, beat, Postgres, Redis)
- **Automated tests**: 67 backend pytest tests (including a real multi-threaded
  overselling-prevention test against PostgreSQL), 16 frontend unit tests, and a
  full-journey end-to-end test of the React app against the live API
  (browse → sign up → cart → checkout → order tracking → sign out)
- **React storefront** (Vite + React Router, mobile-first): home, shop with
  URL-driven filters/sort/search/pagination, product pages with size & colour
  pickers, cart drawer + page, checkout (saved addresses, COD, delivery estimate),
  order history with a progress tracker, account area (profile, addresses,
  password), auth flows incl. password reset

## Tech stack

Python 3.12 · Django 5.2 LTS · Django REST Framework · PostgreSQL 16 ·
SimpleJWT · django-axes · drf-spectacular · django-filter · Celery + Redis ·
Gunicorn · WhiteNoise · Docker · React 19 · Vite · React Router · Vitest

## Project structure

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

Apps planned for later phases (payments gateways beyond COD, coupons,
wishlist, reviews, notifications, reporting) follow the same
`models / services / selectors / api/customer/ / tests` layout, mounted into
`config/api_v1.py` as each one is built.

## Environment setup

**Requirements:** Python 3.12+, PostgreSQL 16, (optionally) Redis and Docker.

### 1. Clone and create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt
```

### 2. PostgreSQL setup

**Linux / macOS:**

```bash
sudo -u postgres psql -c "CREATE ROLE shop WITH LOGIN PASSWORD 'change-me' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE clothing_shop OWNER shop;"
```

**Windows (local development):**

1. Install PostgreSQL 16 from https://www.postgresql.org/download/windows/
   (the installer bundles pgAdmin and the `psql` CLI).
2. Open **SQL Shell (psql)** from the Start menu, connect as the `postgres`
   superuser you set during install, then run:
   ```sql
   CREATE ROLE shop WITH LOGIN PASSWORD 'change-me' CREATEDB;
   CREATE DATABASE clothing_shop OWNER shop;
   ```
3. Confirm the service is running: **Services → postgresql-x64-16 → Running**.
4. Use `DB_HOST=localhost` and `DB_PORT=5432` in `.env`.

This project **requires PostgreSQL from the first migration** — it refuses
to start against SQLite or any non-PostgreSQL engine.

### 3. Environment variables

```bash
cp .env.example .env
```

Generate a real secret key and set it in `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Fill in `DB_*` (or a single `DATABASE_URL`) and `ALLOWED_HOSTS`. Leave
`DEBUG=True` only for local development. **Never commit `.env`.**

### 4. Migrations, demo data, and an admin user

```bash
python manage.py migrate
python manage.py seed_roles          # baseline staff permission groups
python manage.py seed_catalog        # demo categories/products/variants with stock
python manage.py createsuperuser     # your login for /admin/
```

`seed_catalog` is idempotent — safe to re-run; it skips rows that already exist.

### 5. Run everything with one command

```bash
python manage.py runserver
```

- **Storefront**: `http://localhost:8000/`
- **Admin UI**: `http://localhost:8000/admin/`
- API root: `http://localhost:8000/api/v1/`
- Health check: `http://localhost:8000/api/v1/health/`
- Swagger UI: `http://localhost:8000/api/v1/docs/`
- ReDoc: `http://localhost:8000/api/v1/redoc/`

Django serves the **built** React app (same-origin with the API, no CORS setup
needed) and Django Admin. Build the frontend once first:

```bash
cd frontend && npm install && npm run build      # needs Node 20+
```

(Without a build, `/` shows a friendly "storefront not built" page; the API and
admin work regardless.) For day-to-day frontend work use the hot-reloading dev
server instead — it proxies `/api`, `/media` and `/admin` to Django:

```bash
python manage.py runserver            # terminal 1 (backend on :8000)
cd frontend && npm run dev             # terminal 2 -> http://localhost:5173
```

Celery runs in-process (`CELERY_TASK_ALWAYS_EAGER=True` by default in dev),
so no Redis/worker is required to exercise the API locally.

## The shopping flow, end to end

1. **Register/login** → `/api/v1/auth/register/` or `/login/`, returns JWTs
2. **Browse** → `GET /api/v1/products/?category=panjabi&ordering=sort_price`
3. **View one product** → `GET /api/v1/products/{slug}/` (includes variants with live availability)
4. **Add to cart** → `POST /api/v1/cart/items/` with a `variant_id` and `quantity`
   — stock is checked against the real variant row, never trusted from the client
5. **Save an address** → `POST /api/v1/addresses/`
6. **Check out** → `POST /api/v1/checkout/` with `address_id` and an
   `Idempotency-Key` header. This is the most carefully built part of the
   system:
   - Every affected product-variant row is locked (`SELECT ... FOR UPDATE`)
     in a stable order before stock is checked, so two simultaneous
     checkouts for the last unit of stock can't both succeed. Verified with
     a real multi-threaded test (`apps/orders/tests/test_checkout.py::TestConcurrentCheckout`)
     against real PostgreSQL — not a simulation.
   - Retrying the same `Idempotency-Key` returns the original order instead
     of creating a duplicate; the same key with a different request body is
     rejected (409) rather than silently ignored.
   - Prices are recomputed from the current product price at checkout time,
     never from whatever the cart showed earlier.
   - Order line items snapshot the product name/SKU/price at purchase time,
     so editing or discontinuing a product later never corrupts past orders.
7. **View order history** → `GET /api/v1/orders/` and `/api/v1/orders/{uuid}/`

## Admin UI (Django Admin)

Visit `/admin/` and log in with a superuser. From there:
- **Products**: add/edit with inline size/color/stock variant rows right on
  the product page, autocomplete category picker, search by name/SKU
- **Orders**: see every order with inline line items and a full status
  history; changing the `status` dropdown and saving goes through the same
  validated state machine the API uses (e.g. you can't skip straight from
  Pending to Delivered) and automatically marks COD orders as paid on delivery
- **Categories / Variants / Addresses / Users**: standard list/search/filter
  admin views

This is the real admin interface for this stage of the project — fast to use
today, not a mockup — consistent with the original plan to have Django Admin
cover internal management before/alongside any future custom admin dashboard.

## Running tests

```bash
pytest                  # full backend suite, real PostgreSQL via config.settings.test
pytest -v                # verbose
pytest apps/orders        # one app
pytest -k "checkout"       # by keyword
pytest -m concurrency       # just the real multi-threaded overselling test
```

Tests use real PostgreSQL (never SQLite) via Django's standard throwaway
`test_<DB_NAME>` database, and a fast MD5 password hasher (never the Argon2
hasher used in dev/prod — asserted separately by a dedicated test).

### Frontend tests

```bash
cd frontend
npm test                  # 16 fast unit tests (API client, formatting, components) - no server needed
E2E=1 npm test            # + the full-journey test against a LIVE backend
```

The end-to-end test renders the real React app and drives it like a user
(browse, filter, sign up, pick size/colour, add to cart, check out with COD,
track the order, manage addresses, sign out) against a running Django +
PostgreSQL stack. It needs the backend up on `http://127.0.0.1:8000` with demo
data (`python manage.py seed_catalog`); point it elsewhere with `TEST_API_BASE`.

## API documentation

Full OpenAPI 3 schema at `/api/v1/schema/`, interactive docs at
`/api/v1/docs/` (Swagger) and `/api/v1/redoc/` (ReDoc). All 20 endpoints
document their auth requirement, request body, and response codes;
`drf-spectacular --fail-on-warn` passes with zero warnings.

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | none | Create a customer account, returns tokens |
| POST | `/api/v1/auth/login/` | none | Login with email or phone, returns tokens |
| POST | `/api/v1/auth/logout/` | Bearer | Blacklist a refresh token |
| POST | `/api/v1/auth/token/refresh/` | none | Rotate access/refresh tokens |
| POST | `/api/v1/auth/change-password/` | Bearer | Change password, invalidates other sessions |
| POST | `/api/v1/auth/forgot-password/` | none | Request a reset link (always 200, no enumeration) |
| POST | `/api/v1/auth/reset-password/` | none | Complete reset with uid/token from the email |
| GET/PATCH | `/api/v1/profile/` | Bearer | View/update the caller's own profile |
| GET | `/api/v1/categories/` | none | List active categories |
| GET | `/api/v1/products/` | none | List products — filter/search/sort/paginate |
| GET | `/api/v1/products/{slug}/` | none | Product detail with variants |
| GET | `/api/v1/cart/` | Bearer | Get the caller's cart |
| DELETE | `/api/v1/cart/` | Bearer | Clear the cart |
| POST | `/api/v1/cart/items/` | Bearer | Add a variant to the cart |
| PATCH/DELETE | `/api/v1/cart/items/{uuid}/` | Bearer | Update/remove one cart item |
| GET/POST | `/api/v1/addresses/` | Bearer | List/create saved addresses |
| GET/PATCH/DELETE | `/api/v1/addresses/{uuid}/` | Bearer | Manage one address |
| POST | `/api/v1/addresses/{uuid}/set-default/` | Bearer | Mark an address as default |
| POST | `/api/v1/checkout/` | Bearer | Place a COD order (requires `Idempotency-Key` header) |
| GET | `/api/v1/orders/` | Bearer | List the caller's orders |
| GET | `/api/v1/orders/{uuid}/` | Bearer | Order detail with line items |
| GET | `/api/v1/health/` | none | Liveness + DB connectivity check |

Every successful response is enveloped as:
```json
{"success": true, "message": "...", "data": {...}}
```
and every error as:
```json
{"success": false, "message": "...", "errors": {...}, "code": "..."}
```

## Docker

```bash
cp .env.example .env     # fill in a real SECRET_KEY etc.
docker compose up --build
```

This starts `db` (PostgreSQL), `redis`, `web` (Gunicorn, runs migrations and
collectstatic on boot), `worker` (Celery), and `beat` (Celery scheduler).
Run `python manage.py seed_catalog` inside the `web` container afterward to
populate demo products:

```bash
docker compose exec web python manage.py seed_catalog
```

For a production-like run:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Production deployment

See [Render deployment instructions](docs/RENDER_DEPLOYMENT.md) for the Docker
web service, PostgreSQL/TLS environment, CORS/CSRF, SMTP, static files, media
disk, and safe migration workflow. The React storefront is built in the
Dockerfile and served by Django on the same origin. Use `.env.example` for local
development; production secrets belong in Render's environment settings.

## Environment variables

See `.env.example` for local-development values and `.env.production.example`
for a secret-free production variable template. Never commit populated `.env`
files or put backend credentials in frontend `VITE_*` variables.
## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Project setup, PostgreSQL, custom User, JWT auth, core utilities | ✅ Done |
| 2 | Categories, Products, Variants | ✅ Done (image gallery/multi-image still single-image for now) |
| 3 | Inventory, oversell prevention | ✅ Done (direct locked stock decrement; no separate reservation/expiry ledger yet) |
| 4 | Cart, Addresses | ✅ Done |
| 5 | Orders, Checkout | ✅ Done (COD only) |
| 6 | Payments (gateway abstraction beyond COD) | Planned |
| 7 | Coupons, Wishlist, Reviews | Planned |
| 8 | Admin REST APIs, Dashboard/reporting APIs | Planned (Django Admin covers management today) |
| 9 | Notifications (order emails/SMS) | Planned |
| 10 | Further performance/security hardening | Ongoing |
| 11 | Final production polish | Planned |
| — | React storefront (customer UI) | ✅ Done |

## Security notes

- Passwords hashed with Argon2 (PBKDF2 fallback for verification only)
- JWT access tokens are short-lived (15 min default); refresh tokens rotate
  and are blacklisted on logout, password change, and password reset
- django-axes locks out repeated failed logins per IP+identifier
- Every endpoint is private by default (`DEFAULT_PERMISSION_CLASSES =
  IsAuthenticated`); public endpoints opt out explicitly with `AllowAny`
- `/auth/forgot-password/` never reveals whether an identifier is registered
- A customer can never set their own `role`, `email`, `phone_number`, or
  `is_staff` through `/profile/`; `cost_price` is never serialized to customers
- Another user's cart, address, or order 404s rather than 403s — existence
  is never revealed
- Checkout prices and stock are always recomputed/re-verified server-side;
  nothing from the client (price, discount, stock) is ever trusted
- No stack traces, SQL errors, or secrets are ever returned to the client
