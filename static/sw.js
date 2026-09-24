/**
 * SSITS Attendance & Alert Portal - Service Worker
 * High-Performance Offline Caching & Progressive Web App Engine
 */

const CACHE_NAME = 'ssits-portal-v1';

const STATIC_PRECACHE = [
  '/',
  '/static/css/style.css',
  '/static/images/college_logo.png',
  '/static/images/naac_logo.png',
  '/static/images/pwa-icon-192.png',
  '/static/images/pwa-icon-512.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js'
];

// Install Event: Pre-cache static shell assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_PRECACHE).catch((err) => {
        console.warn('[SW] Some assets failed to pre-cache:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate Event: Clean up old cache versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            console.log('[SW] Clearing old cache:', name);
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event: Smart network/cache strategy
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 1. Non-GET requests (POST, PUT, DELETE) and API mutations -> Straight to network
  if (req.method !== 'GET') {
    return;
  }

  // 2. Sensitive dynamic API calls -> Network first, do not cache
  if (url.pathname.startsWith('/api/save') || 
      url.pathname.startsWith('/admin/api/reset') ||
      url.pathname.startsWith('/admin/api/backup') ||
      url.pathname.startsWith('/admin/api/restore')) {
    return;
  }

  // 3. Static Assets (CSS, JS, Fonts, Images) -> Stale-While-Revalidate (Instant load)
  if (
    url.pathname.startsWith('/static/') ||
    url.hostname.includes('cdn.jsdelivr.net') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com')
  ) {
    event.respondWith(
      caches.match(req).then((cachedResponse) => {
        const fetchPromise = fetch(req).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(req, responseToCache);
            });
          }
          return networkResponse;
        }).catch(() => cachedResponse);

        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // 4. HTML Navigation Requests -> Network-First (Live Data), Cache Fallback if Offline
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(req, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          // If offline, attempt to serve cached page
          return caches.match(req).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            return new Response(
              `<!DOCTYPE html>
              <html lang="en">
              <head>
                <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>SSITS Portal - Offline Mode</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
              </head>
              <body class="bg-dark text-white d-flex align-items-center justify-content-center min-vh-100 p-3 text-center">
                <div class="card bg-secondary text-white p-4 shadow" style="max-width: 420px; border-radius: 16px;">
                  <h3 class="fw-bold mb-2">📡 No Internet Connection</h3>
                  <p class="text-white-50 small mb-3">You are currently offline. Please check your WiFi or mobile data connection to access live attendance and records.</p>
                  <button class="btn btn-warning fw-bold w-100" onclick="window.location.reload()">Retry Connection</button>
                </div>
              </body>
              </html>`,
              { headers: { 'Content-Type': 'text/html' } }
            );
          });
        })
    );
  }
});
