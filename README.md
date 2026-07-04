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

## Local development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
mkdir -p data
export SL_ALLOW_DEV_SECRET=1
export SECRET_KEY=dev-local-secret-change-me
export HOST_PASSWORD=dev-host-password
export APP_BASE_URL=http://127.0.0.1:5000
export BEHIND_PROXY=0
uv run flask --app wsgi run --debug
```

Or with Docker:

```bash
docker compose -f docker-compose.local.yml up --build
```

Open http://localhost:8080

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
| Host login | `/host/login` | Host authentication |
| Host dashboard | `/host/` | Manage all lists |
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
