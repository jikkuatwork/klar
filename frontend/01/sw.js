/**
 * Klar - Service Worker for PWA
 */

const CACHE_NAME = 'klar-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/app.css',
  '/assets/logo.svg',
  '/assets/cities.json',
  '/data.csv',
  '/manifest.json',
  // JS files
  '/js/utils/helpers.js',
  '/js/utils/format.js',
  '/js/utils/csv.js',
  '/js/store.js',
  '/js/state.js',
  '/js/router.js',
  '/js/components/toast.js',
  '/js/components/header.js',
  '/js/components/tabs.js',
  '/js/components/filters.js',
  '/js/components/modal.js',
  '/js/components/add-record.js',
  '/js/pages/dashboard.js',
  '/js/pages/list.js',
  '/js/pages/map.js',
  '/js/pages/charts.js',
  '/js/pages/saved.js',
  '/js/pages/chat.js',
  '/js/pages/settings.js',
  '/js/app.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Klar SW: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip external requests (CDNs)
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200) {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            // Add to cache
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          });
      })
  );
});
