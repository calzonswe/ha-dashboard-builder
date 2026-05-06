/**
 * HA Dashboard Builder Service Worker
 * Uses stale-while-revalidate strategy for content, cache-first for static assets
 */

const CACHE_NAME = 'ha-dashboard-builder-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
]

// Install event - cache static assets immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS)
    }),
  )
  // Activate immediately to skip waiting
  self.skipWaiting()
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name)),
      )
    }),
  )
  // Claim all clients immediately
  self.clients.claim()
})

// Fetch event - serve from cache, update in background
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // For API requests, use stale-while-revalidate strategy
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/ws')) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          // Return cached response immediately
          const fetchPromise = fetch(event.request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(event.request, networkResponse.clone())
            }
            return networkResponse
          }).catch(() => {
            // Network failure - fall back to cached response or offline page
            return cachedResponse || new Response('Offline', { status: 503 })
          })

          return cachedResponse || fetchPromise
        })
      }),
    )
  } else {
    // For static assets, use cache-first strategy
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse
        }

        return fetch(event.request).then((networkResponse) => {
          // Cache the response for future use
          const responseToCache = networkResponse.clone()
          caches.put(event.request, responseToCache)
          return networkResponse
        }).catch(() => {
          // If both cache and network fail, serve a fallback
          return new Response('', { status: 404 })
        })
      }),
    )
  }
})

// Handle messages from clients (e.g., skipWaiting, activate)
self.addEventListener('message', (event) => {
  const { action } = event.data || {}

  if (action === 'skipWaiting') {
    self.skipWaiting()
  } else if (action === 'clearCache') {
    caches.keys().then((cacheNames) => {
      cacheNames.forEach((name) => caches.delete(name))
    })
  }
})
