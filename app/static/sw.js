// CAMINHO: app/static/sw.js
// ⚠️  Este arquivo precisa ser servido em /sw.js (raiz) pelo Flask
//     Veja a rota em: app/routes/pwa.py

const CACHE_NAME = 'launcher-v1';
const OFFLINE_URL = '/offline';

// Páginas e assets que serão cacheados imediatamente na instalação
const PRECACHE_URLS = [
  '/',
  '/dashboard',
  '/simulados',
  '/offline',
  '/static/css/style.css',
  '/static/css/bottom-nav.css',
  '/static/js/main.js',
  '/static/images/favicon.png',
  '/static/images/icons/icon-192x192.png',
];

// ─────────────────────────────────────────────
// INSTALL: pré-cacheia os recursos essenciais
// ─────────────────────────────────────────────
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pré-cacheando recursos essenciais');
      return cache.addAll(PRECACHE_URLS);
    }).then(() => self.skipWaiting())
  );
});

// ─────────────────────────────────────────────
// ACTIVATE: limpa caches antigos
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
    }).then(() => self.clients.claim())
  );
});

// ─────────────────────────────────────────────
// FETCH: estratégia Network First com fallback para cache
// ─────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  // Ignora requisições não-GET e requests de APIs externas
  if (event.request.method !== 'GET') return;
  if (!event.request.url.startsWith(self.location.origin)) return;

  // Ignora chamadas de API do Flask (sempre busca rede)
  const apiPaths = ['/api/', '/webhook/', '/health'];
  const url = new URL(event.request.url);
  if (apiPaths.some(path => url.pathname.startsWith(path))) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clona e cacheia a resposta bem-sucedida
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline: tenta servir do cache
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // Se for navegação (página HTML), mostra página offline
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
        });
      })
  );
});

// ─────────────────────────────────────────────
// PUSH NOTIFICATIONS (Firebase Cloud Messaging)
// ─────────────────────────────────────────────
self.addEventListener('push', (event) => {
  console.log('[SW] Push recebido:', event);

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

  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    vibrate: [200, 100, 200],
    data: { url: data.url },
    actions: data.actions || [],
    requireInteraction: data.requireInteraction || false,
    tag: data.tag || 'launcher-notification',
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// ─────────────────────────────────────────────
// NOTIFICATION CLICK: abre a URL correta ao clicar
// ─────────────────────────────────────────────
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada:', event.notification);
  event.notification.close();

  const targetUrl = event.notification.data?.url || '/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Se o app já está aberto, foca nele
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      // Senão, abre uma nova janela
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// ─────────────────────────────────────────────
// BACKGROUND SYNC (futuro: sincronizar dados offline)
// ─────────────────────────────────────────────
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  if (event.tag === 'sync-progresso') {
    event.waitUntil(syncProgressoOffline());
  }
});

async function syncProgressoOffline() {
  // Placeholder para sincronização futura de progresso offline
  console.log('[SW] Sincronizando progresso offline...');
}
