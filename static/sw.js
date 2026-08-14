const CACHE_NAME = 'duospeak-v2.0';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((k) => caches.delete(k)));
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  // Always fetch fresh network for HTML, JS, CSS, and API endpoints
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
