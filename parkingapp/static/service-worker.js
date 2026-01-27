// Smart Parking - Progressive Web App Service Worker
// Enables offline functionality and app installation

const CACHE_NAME = 'smart-parking-v1';
const RUNTIME_CACHE = 'smart-parking-runtime';
const ASSETS_CACHE = 'smart-parking-assets';

const ESSENTIAL_URLS = [
  '/',
  '/login/',
  '/signup/',
  '/parking-history/',
  '/static/css/bootstrap.min.css',
  '/static/js/jquery.min.js',
  '/static/js/bootstrap.min.js'
];

// Install event - cache essential assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Service Worker: Caching essential URLs');
      return cache.addAll(ESSENTIAL_URLS);
    }).then(() => {
      self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== ASSETS_CACHE) {
            console.log('Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - implement offline-first strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Strategy: Network-first for API calls, Cache-first for static assets
  if (request.url.includes('/api/')) {
    event.respondWith(networkFirstStrategy(request));
  } else if (
    request.url.includes('/static/') ||
    request.url.endsWith('.js') ||
    request.url.endsWith('.css')
  ) {
    event.respondWith(cacheFirstStrategy(request));
  } else {
    event.respondWith(networkFirstStrategy(request));
  }
});

// Cache-first strategy: Try cache first, fallback to network
async function cacheFirstStrategy(request) {
  try {
    const cache = await caches.open(ASSETS_CACHE);
    const cached = await cache.match(request);
    
    if (cached) {
      console.log('Service Worker: Cache hit -', request.url);
      return cached;
    }
    
    const response = await fetch(request);
    
    if (response.ok) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('Service Worker: Fetch failed for', request.url, error);
    
    // Return offline page for HTML requests
    if (request.destination === 'document') {
      return caches.match(ESSENTIAL_URLS[0]);
    }
    
    // Return a generic response for other assets
    return new Response('Resource unavailable while offline', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

// Network-first strategy: Try network, fallback to cache
async function networkFirstStrategy(request) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('Service Worker: Network fetch failed for', request.url);
    
    const cached = await caches.match(request);
    if (cached) {
      console.log('Service Worker: Using cached response for', request.url);
      return cached;
    }
    
    // Return offline response
    if (request.destination === 'document') {
      return caches.match(ESSENTIAL_URLS[0]);
    }
    
    return new Response('Resource unavailable while offline', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

// Background sync - sync when connection is restored
self.addEventListener('sync', event => {
  if (event.tag === 'sync-parking-data') {
    event.waitUntil(syncParkingData());
  }
});

async function syncParkingData() {
  try {
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_START',
        message: 'Synchronizing parking data...'
      });
    });
    
    // Sync pending payments
    const response = await fetch('/api/sync-payments/', {
      method: 'POST'
    });
    
    if (response.ok) {
      clients.forEach(client => {
        client.postMessage({
          type: 'SYNC_COMPLETE',
          message: 'Parking data synchronized'
        });
      });
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Push notifications
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'New notification',
    icon: '/static/images/logo.png',
    badge: '/static/images/badge.png',
    tag: 'parking-notification',
    requireInteraction: true
  };
  
  event.waitUntil(
    self.registration.showNotification('Smart Parking', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(clientList => {
      // Check if parking app is already open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      // If not open, open it
      if (clients.openWindow) {
        return clients.openWindow('/parking-history/');
      }
    })
  );
});

// Message event - receive messages from client
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('Service Worker: Loaded and ready');
