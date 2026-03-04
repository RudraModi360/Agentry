/**
 * AGENTRY UI - Service Worker
 * Caches static assets for fast page reloads (target: 2-3 seconds)
 */

const CACHE_NAME = 'agentry-v1';
const STATIC_CACHE_NAME = 'agentry-static-v1';

// Static assets to cache immediately on install
const STATIC_ASSETS = [
    '/chat.html',
    '/css/main.css',
    '/js/env.js',
    '/js/config.js',
    '/js/utils/dom.js',
    '/js/utils/api.js',
    '/js/utils/storage.js',
    '/js/components/theme.js',
    '/js/components/clock.js',
    '/js/components/sidebar.js',
    '/js/components/messages.js',
    '/js/components/websocket.js',
    '/js/components/modals.js',
    '/js/components/profile-modal.js',
    '/js/components/projects.js',
    '/js/components/tools.js',
    '/js/components/sessions.js',
    '/js/components/upload.js',
    '/js/components/autocorrect.js',
    '/js/components/media.js',
    '/js/components/model-selector.js',
    '/js/components/input-editor.js',
    '/js/main.js',
    '/assets/favicon.ico'
];

// External CDN resources to cache
const CDN_ASSETS = [
    'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js',
    'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css'
];

/**
 * Install event - cache static assets
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    
    event.waitUntil(
        Promise.all([
            // Cache local static assets
            caches.open(STATIC_CACHE_NAME).then((cache) => {
                console.log('[SW] Caching static assets...');
                return cache.addAll(STATIC_ASSETS).catch(err => {
                    console.warn('[SW] Some static assets failed to cache:', err);
                });
            }),
            // Cache CDN assets
            caches.open(CACHE_NAME).then((cache) => {
                console.log('[SW] Caching CDN assets...');
                return Promise.allSettled(
                    CDN_ASSETS.map(url => 
                        fetch(url, { mode: 'cors' })
                            .then(response => {
                                if (response.ok) {
                                    return cache.put(url, response);
                                }
                            })
                            .catch(err => console.warn(`[SW] Failed to cache ${url}:`, err))
                    )
                );
            })
        ]).then(() => {
            console.log('[SW] Installation complete');
            // Skip waiting to activate immediately
            return self.skipWaiting();
        })
    );
});

/**
 * Activate event - cleanup old caches
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME && name !== STATIC_CACHE_NAME)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => {
            console.log('[SW] Activation complete');
            // Take control of all pages immediately
            return self.clients.claim();
        })
    );
});

/**
 * Fetch event - serve from cache with network fallback
 */
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip WebSocket connections
    if (url.protocol === 'wss:' || url.protocol === 'ws:') {
        return;
    }
    
    // Skip API requests - let them go to network
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
        return;
    }
    
    // For static assets, use cache-first strategy
    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(event.request));
        return;
    }
    
    // For HTML pages, use network-first with cache fallback
    if (url.pathname.endsWith('.html') || url.pathname === '/') {
        event.respondWith(networkFirst(event.request));
        return;
    }
    
    // For everything else, try cache first then network
    event.respondWith(cacheFirst(event.request));
});

/**
 * Check if URL is a static asset
 */
function isStaticAsset(url) {
    const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'];
    return staticExtensions.some(ext => url.pathname.endsWith(ext));
}

/**
 * Cache-first strategy - fast for static assets
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        // Return cached version immediately
        // Update cache in background for next time
        updateCacheInBackground(request);
        return cachedResponse;
    }
    
    // Not in cache, fetch from network
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.warn('[SW] Fetch failed:', error);
        // Return a fallback if available
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Network-first strategy - fresh content for HTML
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        // Network failed, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Update cache in background (stale-while-revalidate pattern)
 */
function updateCacheInBackground(request) {
    fetch(request)
        .then(response => {
            if (response.ok) {
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, response);
                });
            }
        })
        .catch(() => {
            // Ignore errors in background update
        });
}

/**
 * Handle messages from the main thread
 */
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
    
    if (event.data === 'clearCache') {
        caches.keys().then((cacheNames) => {
            return Promise.all(cacheNames.map((name) => caches.delete(name)));
        });
    }
});
