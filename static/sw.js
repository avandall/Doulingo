const CACHE_NAME = 'duospeak-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Pass through fetch requests for real-time APIs
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
