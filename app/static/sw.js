const CACHE = "simple-lists-v3";
const STATIC_ASSETS = [
  "/static/style.css",
  "/static/app.js",
  "/static/manifest.webmanifest",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
];

function isStaticAsset(pathname) {
  return pathname.startsWith("/static/");
}

function cacheResponse(request, response) {
  if (response && response.status === 200 && response.type === "basic") {
    const copy = response.clone();
    caches.open(CACHE).then((cache) => cache.put(request, copy));
  }
  return response;
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  // Network-first for everything so UI updates are picked up after deploys.
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (isStaticAsset(url.pathname)) {
          return cacheResponse(event.request, response);
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
