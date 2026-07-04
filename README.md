# Simple Lists

Lightweight shared todo lists — no accounts, just shareable links. The host manages lists behind a container password; participants collaborate via unguessable URLs.

## Features

- Host-only management (password set via `HOST_PASSWORD` when starting the container)
- Multiple simple lists — each item is a string that can be checked off
- Share links with ~256-bit unguessable tokens (`/l/{token}`)
- Optional per-list password on share links
- Export / import all lists as JSON (includes share tokens, items, and list passwords)
- SQLite backend, Docker-ready for Caddy reverse proxy
- Mobile-first UI with Pico CSS
- Installable as a home-screen web app on Android and iOS (PWA manifest + service worker)

## Local development

### Environment file

Local Compose loads settings from a `.env` file in the project root (`env_file` in `docker-compose.local.yml`). Create it once before starting the container:

```bash
cp .env.example .env
```

For local development, set at least:

```env
SECRET_KEY=dev-local-secret-change-me
HOST_PASSWORD=dev-host-password
APP_BASE_URL=http://localhost:8080
SL_ALLOW_DEV_SECRET=1
```

`SL_ALLOW_DEV_SECRET=1` is required when using placeholder secrets locally — the app refuses to start with known dev defaults otherwise. Share links use `APP_BASE_URL`, so keep it aligned with the port you open in the browser.

The SQLite database is stored in `./data` (mounted into the container). Your lists persist across restarts.

### Run with Podman Compose (recommended)

Matches the production container setup on port **8080**:

```bash
mkdir -p data
podman compose -f docker-compose.local.yml up -d --build
```

Open http://localhost:8080 and log in with the `HOST_PASSWORD` from your `.env`.

**After code or template changes**, rebuild and recreate the container (a plain `restart` reuses the old image):

```bash
podman compose -f docker-compose.local.yml up -d --build --force-recreate
```

Stop the stack:

```bash
podman compose -f docker-compose.local.yml down
```

If the UI looks stale after a deploy, hard-refresh the browser (Ctrl+Shift+R) so the service worker and static assets reload.

`docker compose` works the same way if you use Docker instead of Podman.

### Run with uv (Flask dev server)

Requires [uv](https://docs.astral.sh/uv/). Useful for quick Python debugging on port **5000**:

```bash
uv sync
mkdir -p data
cp .env.example .env   # then edit as above; use APP_BASE_URL=http://127.0.0.1:5000
set -a && source .env && set +a
uv run flask --app wsgi run --debug
```

Open http://127.0.0.1:5000

## Production deployment (Caddy)

Designed to run behind a [caddy_reverse](https://github.com/) stack on the external Docker network `caddy_net`.

### 1. Deploy the app stack

```bash
sudo deploy-app simple-lists
cd /opt/stacks/simple-lists
cp .env.example .env   # set SECRET_KEY, HOST_PASSWORD, and APP_BASE_URL
docker compose up -d --build
```

Ensure `.env` contains:

```env
SECRET_KEY=<long-random-string>
HOST_PASSWORD=<your-host-password>
APP_BASE_URL=https://simple-lists.<your-apps-domain>
```

### 2. Add Caddy site block

```caddyfile
simple-lists.${APPS_DOMAIN} {
    reverse_proxy simple-lists:8080
}
```

**No basic auth on Caddy** — participants must reach share links without a gate password. The host area is protected by `HOST_PASSWORD`; share links rely on unguessable tokens (and optional per-list passwords).

### 3. DNS

Ensure `simple-lists` is covered by your wildcard `*.${APPS_DOMAIN}` record.

## URL model

| Link | Path | Purpose |
|------|------|---------|
| Landing | `/` | Private-app info and owner login |
| Host dashboard | `/host/` | Manage all lists (after login) |
| Share link | `/l/{share_token}` | Collaborate on a list |

Keep share links private — they are the primary access control for participants.

## Export format

```json
{
  "version": 1,
  "exported_at": "2026-07-04T12:00:00+00:00",
  "lists": [
    {
      "title": "Groceries",
      "share_token": "...",
      "locked": true,
      "password": "optional-list-password",
      "items": [
        { "text": "Milk", "completed": false }
      ]
    }
  ]
}
```

## Environment variables

Copy `.env.example` to `.env` for local development. Compose (`docker-compose.local.yml`) reads this file automatically; production deployment uses the same pattern.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required in prod) | Flask secret for sessions/CSRF |
| `HOST_PASSWORD` | (required in prod) | Password for host management area |
| `APP_BASE_URL` | request root | Public base URL for share links |
| `DATABASE_URL` | `./data/simple_lists.db` | SQLite connection string |
| `BEHIND_PROXY` | `1` | Enable ProxyFix for Caddy |
| `SL_ALLOW_DEV_SECRET` | unset | Set to `1` for local dev with placeholder secrets |

Production requires a strong `SECRET_KEY` and `HOST_PASSWORD`. The app refuses to start with known dev defaults unless `SL_ALLOW_DEV_SECRET=1`.

## License

MIT
