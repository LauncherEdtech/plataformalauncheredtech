// ⚠️  Este arquivo precisa ser servido em /sw.js (raiz) pelo Flask
//     Veja a rota em: app/routes/pwa.py

const CACHE_NAME = 'launcher-v2';
const OFFLINE_URL = '/pwa/offline';

// ⚠️ IMPORTANTE: Coloque aqui APENAS arquivos que existem com certeza.
// Se qualquer URL falhar com cache.addAll(), o SW inteiro aborta a instalação
// e o getToken() do FCM nunca executa (serviceWorker.ready fica travado).
const PRECACHE_URLS = [
  '/static/css/style.css',
  '/static/css/bottom-nav.css',
  '/static/js/main.js',
];

// ─────────────────────────────────────────────
// INSTALL
// ─────────────────────────────────────────────
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando Service Worker v2...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // ✅ Promise.allSettled: continua mesmo se algum recurso falhar
      return Promise.allSettled(
        PRECACHE_URLS.map(url =>
          cache.add(url).catch(err => {
            console.warn('[SW] Não cacheou (ignorando):', url, err.message);
          })
        )
      );
    }).then(() => {
      console.log('[SW] Instalação OK. Ativando imediatamente...');
      return self.skipWaiting();
    })
  );
});

// ─────────────────────────────────────────────
// ACTIVATE
// ─────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  console.log('[SW] Ativando Service Worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deletando cache antigo:', name);
            return caches.delete(name);
          })
      );
    }).then(() => {
      console.log('[SW] Ativo. Assumindo controle de todas as abas...');
      return self.clients.claim();
    })
  );
});

// ─────────────────────────────────────────────
// FETCH: Network First com fallback para cache
// ─────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  if (!event.request.url.startsWith(self.location.origin)) return;

  const apiPaths = ['/api/', '/webhook/', '/health', '/pwa/salvar-token', '/pwa/remover-token'];
  const url = new URL(event.request.url);
  if (apiPaths.some(path => url.pathname.startsWith(path))) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
        });
      })
  );
});

// ─────────────────────────────────────────────
// PUSH NOTIFICATIONS
// ─────────────────────────────────────────────
self.addEventListener('push', (event) => {
  console.log('[SW] Push recebido');

  let data = {
    title: 'Launcher Educação',
    body: 'Você tem uma nova notificação!',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/icon-72x72.png',
    url: '/dashboard',
  };

  try {
    if (event.data) {
      const payload = event.data.json();
      data = { ...data, ...payload };
    }
  } catch (e) {
    console.error('[SW] Erro ao parsear payload:', e);
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      vibrate: [200, 100, 200],
      data: { url: data.url },
      tag: data.tag || 'launcher-notification',
      requireInteraction: data.requireInteraction || false,
    })
  );
});

// ─────────────────────────────────────────────
// NOTIFICATION CLICK
// ─────────────────────────────────────────────
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-progresso') {
    event.waitUntil(Promise.resolve());
  }
});
