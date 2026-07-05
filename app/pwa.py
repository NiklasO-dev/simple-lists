from flask import Response, jsonify

MANIFEST_ICONS = [
    {
        "src": "/static/icons/icon-192.png",
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "any",
    },
    {
        "src": "/static/icons/icon-512.png",
        "sizes": "512x512",
        "type": "image/png",
        "purpose": "any",
    },
    {
        "src": "/static/icons/icon-512.png",
        "sizes": "512x512",
        "type": "image/png",
        "purpose": "maskable",
    },
]


def manifest_response(*, name: str, short_name: str, start_url: str, manifest_id: str | None = None) -> Response:
    payload = {
        "id": manifest_id or start_url,
        "name": name,
        "short_name": short_name,
        "description": "Private shared lists — add to your home screen for quick access.",
        "start_url": start_url,
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": "#ffffff",
        "theme_color": "#0f6cbd",
        "icons": MANIFEST_ICONS,
    }
    response = jsonify(payload)
    response.headers["Cache-Control"] = "no-cache"
    return response
