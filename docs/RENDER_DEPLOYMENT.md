# Deploying this project on Render

This repository builds a single Docker web service: the Dockerfile compiles the
React storefront and Django serves it at `/`; Django also serves `/api/v1/`,
`/admin/`, `/static/`, and `/media/`. Keep the existing JWT authentication,
PostgreSQL schema, and filesystem media storage.

## Render service

1. Push the repository to a Git provider and create a Render **Web Service**
   from it. Select **Docker** and the repository root as the Docker context.
2. Set the health check path to `/api/v1/health/`.
3. Add a persistent disk mounted at `/app/media`. `MEDIA_ROOT` defaults to this
   location in production. Render's service filesystem is otherwise ephemeral;
   persistent disks are available on paid services and keep local uploads
   across deploys. Keep this mount path stable to preserve existing `/media/...`
   URLs.
4. Set the environment variables below in the Render dashboard. Do not commit
   `.env`, `.env.production`, or any credentials.
5. Use this start command:

   ```sh
   python manage.py collectstatic --noinput && gunicorn -c gunicorn.conf.py config.wsgi:application
   ```

   The Dockerfile already builds the React app. The start command collects
   Django static assets on each instance start; it does not run migrations.

## Required environment variables

- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `DEBUG=False`
- `SECRET_KEY`: unique random value, at least 50 characters
- `ALLOWED_HOSTS`: comma-separated exact Render hostname and custom domains
- `DATABASE_URL`: Render PostgreSQL **internal** connection URL
- `FRONTEND_URL`: canonical `https://` storefront origin
- `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`: comma-separated full
  `https://` origins. The default single-service app is same-origin; include
  each custom frontend origin if it differs.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL` from your SMTP provider.
- `MEDIA_ROOT=/app/media` and `SERVE_MEDIA=True` when using the attached disk.
- `SECURE_SSL_REDIRECT=True`.

Production settings use `DATABASE_URL` ahead of `DB_NAME`/`DB_USER`/`DB_PASSWORD`
and require PostgreSQL TLS (`sslmode=require`). Never expose `DATABASE_URL`,
`SECRET_KEY`, SMTP credentials, or other secrets through `VITE_*` variables;
Vite embeds those values in browser assets.

## Existing product images and database safety

Database rows store media-relative paths, and the project uses Django's existing
filesystem storage. Keeping the `/app/media` mount preserves those paths and
serves the same `/media/...` URLs. A new Render disk starts empty: before
switching traffic, copy the existing media directory into the disk while
preserving relative paths, then verify representative product images. Do not
change product records or switch storage backends as part of that transfer.

No migration is run automatically at startup. Before applying reviewed
migrations to an existing database, take a database backup using the provider's
backup facility or `pg_dump`, inspect `python manage.py showmigrations` and the
migration plan, then apply only the reviewed migrations during a controlled
release. Never run `flush`, reset, or seed commands against production data.

## Separate frontend hosting

The default Docker deployment serves React and Django from one origin, so
`VITE_API_BASE` remains `/api/v1`. If you split the frontend into a Render Static
Site, set its build-time `VITE_API_BASE` to the public API origin plus
`/api/v1`, then add the frontend's exact HTTPS origin to Django's CORS and CSRF
settings. Never put backend secrets in frontend build variables.

Use `.env.example` for local development and `.env.production.example` only as
a list of production variable names; configure actual values in Render.
