/* eslint-disable no-restricted-globals */
const STATIC_CACHE = 'cryptoai-static-v2';

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(caches.open(STATIC_CACHE));
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((key) => {
      if (key !== STATIC_CACHE) {
        return caches.delete(key);
      }
      return Promise.resolve();
    }));
    await self.clients.claim();
  })());
});

function isApiRequest(url) {
  return url.origin === 'https://api.dacryptobeast.com' || url.pathname.startsWith('/api/');
}

function isOffline() {
  return typeof self.navigator !== 'undefined' && self.navigator.onLine === false;
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (!request || request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  // Never cache API calls. Always try network first and provide a safe fallback.
  if (isApiRequest(url)) {
    event.respondWith((async () => {
      try {
        return await fetch(request);
      } catch (_error) {
        if (!isOffline()) {
          throw _error;
        }

        return new Response(
          JSON.stringify({ detail: 'Network unavailable', source: 'service-worker-fallback' }),
          {
            status: 503,
            headers: {
              'Content-Type': 'application/json',
              'Cache-Control': 'no-store',
            },
          },
        );
      }
    })());
    return;
  }

  // Network-first for navigations so deploys are reflected quickly.
  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const networkResponse = await fetch(request);
        return networkResponse;
      } catch (_error) {
        const fallback = await caches.match('/index.html');
        if (fallback) {
          return fallback;
        }
        throw _error;
      }
    })());
    return;
  }

  // Static assets: cache-first with network refresh.
  event.respondWith((async () => {
    if (url.pathname === '/sw.js') {
      return fetch(request);
    }

    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }

    const response = await fetch(request);
    if (response && response.ok && url.origin === self.location.origin) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  })());
});
