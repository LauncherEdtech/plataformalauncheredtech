// CAMINHO: app/static/js/pwa.js

// ─────────────────────────────────────────────
// CONFIGURAÇÃO FIREBASE
// ─────────────────────────────────────────────
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyDsymFEW3dOAZIktTqq1aBl1A3ieqmqc_8",
  authDomain: "launcher-educacao.firebaseapp.com",
  projectId: "launcher-educacao",
  storageBucket: "launcher-educacao.firebasestorage.app",
  messagingSenderId: "411831431678",
  appId: "1:411831431678:web:e648587d06a165c79190af",
};

const VAPID_KEY = "BL6LH47A1OVQuOX5_Y3eGAW_nT_2pyfv9jiiCZHT9CkugzUdBvSJ6qSXhMpcf3FuYV7aExKhwXiwMD732uItw8o";

// ─────────────────────────────────────────────
// 1. REGISTRAR SERVICE WORKER
// ─────────────────────────────────────────────
async function registrarServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    console.warn('[PWA] Service Worker não suportado neste navegador.');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });
    console.log('[PWA] Service Worker registrado. Scope:', registration.scope);
    setInterval(() => registration.update(), 60 * 1000);
    return registration;
  } catch (err) {
    console.error('[PWA] Erro ao registrar Service Worker:', err);
    return null;
  }
}

// ─────────────────────────────────────────────
// 2. INICIALIZAR FIREBASE + FCM
// ─────────────────────────────────────────────
async function inicializarFCM() {
  if (!('Notification' in window)) {
    console.warn('[FCM] Notificações não suportadas neste navegador.');
    return null;
  }

  try {
    const { initializeApp, getApps } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js');
    const { getMessaging, onMessage } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging.js');

    // Evita inicializar o Firebase duas vezes
    const firebaseApp = getApps().length === 0
      ? initializeApp(FIREBASE_CONFIG)
      : getApps()[0];

    const messaging = getMessaging(firebaseApp);

    onMessage(messaging, (payload) => {
      console.log('[FCM] Mensagem em foreground:', payload);
      mostrarNotificacaoForeground(payload);
    });

    return messaging;
  } catch (err) {
    console.error('[FCM] Erro ao inicializar Firebase:', err);
    return null;
  }
}

// ─────────────────────────────────────────────
// 3. SOLICITAR PERMISSÃO E SALVAR TOKEN FCM
// ─────────────────────────────────────────────
async function solicitarPermissaoNotificacao(messaging) {
  if (!messaging) return;

  try {
    // ✅ Se já está bloqueado pelo usuário, orienta sem tentar requestPermission
    // (requestPermission com 'denied' retorna 'denied' sem mostrar nenhum prompt)
    if (Notification.permission === 'denied') {
      console.warn('[FCM] Permissão bloqueada. Usuário precisa habilitar manualmente.');
      mostrarAvisoPermissaoBloqueada();
      return;
    }

    const permissao = await Notification.requestPermission();

    if (permissao !== 'granted') {
      console.warn('[FCM] Permissão negada pelo usuário.');
      return;
    }

    console.log('[FCM] Permissão concedida! Obtendo token...');

    const { getToken } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging.js');

    // Aguarda o SW estar pronto antes de pedir token
const swRegistration = await navigator.serviceWorker.register('/firebase-messaging-sw.js', {
    scope: '/firebase-cloud-messaging-push-scope'
});
await navigator.serviceWorker.ready;

    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY,
      serviceWorkerRegistration: swRegistration,
    });

    if (token) {
      console.log('[FCM] Token obtido:', token.substring(0, 30) + '...');
      await salvarTokenNoServidor(token);
    } else {
      console.warn('[FCM] Nenhum token gerado. Verifique a configuração VAPID.');
    }
  } catch (err) {
    console.error('[FCM] Erro ao solicitar permissão/token:', err);
  }
}

// ─────────────────────────────────────────────
// 4. AVISO QUANDO PERMISSÃO ESTÁ BLOQUEADA
// ─────────────────────────────────────────────
function mostrarAvisoPermissaoBloqueada() {
  // Não duplica
  if (document.getElementById('pwa-notif-bloqueada')) return;

  const aviso = document.createElement('div');
  aviso.id = 'pwa-notif-bloqueada';
  aviso.style.cssText = `
    position: fixed;
    bottom: 90px;
    left: 50%;
    transform: translateX(-50%);
    background: #1a1a2e;
    border: 1px solid #f59e0b;
    border-radius: 14px;
    padding: 16px 20px;
    max-width: 340px;
    width: 90%;
    z-index: 9999;
    text-align: center;
    color: white;
    font-size: 13px;
    box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
    animation: pwaFadeIn 0.3s ease;
  `;
  aviso.innerHTML = `
    <style>
      @keyframes pwaFadeIn { from { opacity:0; transform: translateX(-50%) translateY(10px); } to { opacity:1; transform: translateX(-50%) translateY(0); } }
    </style>
    <div style="font-size:28px; margin-bottom:8px;">🔕</div>
    <strong style="font-size:14px;">Notificações bloqueadas</strong>
    <p style="color:#a3a3a3; margin:8px 0 0; line-height:1.5;">
      Para ativar, clique no <strong style="color:white;">🔒 cadeado</strong> na barra de endereço
      → <strong style="color:white;">Notificações</strong> → <strong style="color:white;">Permitir</strong>
      e recarregue a página.
    </p>
    <button onclick="document.getElementById('pwa-notif-bloqueada').remove()"
      style="margin-top:12px; background:#f59e0b; color:#000; border:none; border-radius:8px; padding:8px 20px; font-weight:600; cursor:pointer; font-size:13px;">
      Entendi
    </button>
  `;
  document.body.appendChild(aviso);
  setTimeout(() => aviso?.remove(), 20000);
}

// ─────────────────────────────────────────────
// 5. ENVIAR TOKEN PARA O BACKEND FLASK
// ─────────────────────────────────────────────
async function salvarTokenNoServidor(token) {
  try {
    const response = await fetch('/pwa/salvar-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': obterCSRFToken(),
      },
      body: JSON.stringify({
        token: token,
        plataforma: detectarPlataforma(),
        user_agent: navigator.userAgent,
      }),
    });

    // Verifica se a resposta é JSON antes de parsear
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      console.error('[FCM] Servidor retornou resposta não-JSON. Status:', response.status);
      return;
    }

    const data = await response.json();
    if (data.success) {
      console.log('[FCM] ✅ Token salvo no servidor com sucesso!');
    } else {
      console.warn('[FCM] Erro ao salvar token:', data.error);
    }
  } catch (err) {
    console.error('[FCM] Erro na requisição para salvar token:', err);
  }
}

// ─────────────────────────────────────────────
// 6. NOTIFICAÇÃO EM FOREGROUND (app aberto)
// ─────────────────────────────────────────────
function mostrarNotificacaoForeground(payload) {
  const title = payload.notification?.title || 'Launcher Educação';
  const body  = payload.notification?.body  || '';
  const url   = payload.data?.url           || '/dashboard';

  const toast = document.createElement('div');
  toast.className = 'position-fixed bottom-0 end-0 p-3';
  toast.style.cssText = 'z-index: 9999; min-width: 300px;';
  toast.innerHTML = `
    <div class="toast show" role="alert" style="background:#1a1a2e; border:1px solid #8b5cf6; color:white;">
      <div class="toast-header" style="background:#0a0a1a; color:white; border-bottom:1px solid #8b5cf6;">
        <strong class="me-auto">${title}</strong>
        <button type="button" class="btn-close btn-close-white" onclick="this.closest('.position-fixed').remove()"></button>
      </div>
      <div class="toast-body">
        ${body}
        ${url ? `<div class="mt-2"><a href="${url}" class="btn btn-sm btn-outline-light">Ver →</a></div>` : ''}
      </div>
    </div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 6000);
}

// ─────────────────────────────────────────────
// 7. BOTÃO FIXO DE INSTALAÇÃO (FAB)
// ─────────────────────────────────────────────
let deferredInstallPrompt = null;

window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  console.log('[PWA] Prompt de instalação capturado.');
});

function mostrarBotaoInstalacao() {
  if (localStorage.getItem('pwa_instalado')) return;
  if (window.matchMedia('(display-mode: standalone)').matches) return;
  if (document.getElementById('pwa-fab-install')) return;

  const fab = document.createElement('div');
  fab.id = 'pwa-fab-install';
  fab.style.cssText = `
    position: fixed;
    bottom: 80px;
    right: 16px;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    color: white;
    border-radius: 50px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    z-index: 9997;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.5);
    animation: pwaSlideIn 0.4s ease;
    user-select: none;
  `;
  fab.innerHTML = `
    <style>
      @keyframes pwaSlideIn {
        from { transform: translateX(120px); opacity: 0; }
        to   { transform: translateX(0);     opacity: 1; }
      }
    </style>
    <span style="font-size:16px;">📲</span>
    <span>Instalar App</span>
    <span id="pwa-fab-close" style="margin-left:4px; opacity:0.6; font-size:18px; line-height:1; padding:0 2px;">×</span>
  `;

  document.body.appendChild(fab);

  document.getElementById('pwa-fab-close').addEventListener('click', (e) => {
    e.stopPropagation();
    fab.remove();
  });

  fab.addEventListener('click', async (e) => {
    if (e.target.id === 'pwa-fab-close') return;
    await instalarPWA();
  });
}

async function instalarPWA() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    const { outcome } = await deferredInstallPrompt.userChoice;
    console.log('[PWA] Resultado da instalação:', outcome);
    if (outcome === 'accepted') {
      localStorage.setItem('pwa_instalado', 'true');
      const fab = document.getElementById('pwa-fab-install');
      if (fab) fab.remove();
    }
    deferredInstallPrompt = null;
  } else {
    window.location.href = '/instalar-app';
  }
}

window.addEventListener('appinstalled', () => {
  console.log('[PWA] App instalado com sucesso!');
  localStorage.setItem('pwa_instalado', 'true');
  const fab = document.getElementById('pwa-fab-install');
  if (fab) fab.remove();
});

// ─────────────────────────────────────────────
// 8. UTILITÁRIOS
// ─────────────────────────────────────────────
function obterCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

function detectarPlataforma() {
  const ua = navigator.userAgent;
  if (/android/i.test(ua)) return 'android';
  if (/iPad|iPhone|iPod/.test(ua)) return 'ios';
  return 'desktop';
}

// ─────────────────────────────────────────────
// 9. INICIALIZAÇÃO PRINCIPAL
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {

  // Registra Service Worker
  await registrarServiceWorker();

  // Botão fixo de instalação aparece após 3s
  setTimeout(mostrarBotaoInstalacao, 3000);

  // FCM só para usuários logados
  const isLoggedIn = document.body.dataset.loggedIn === 'true';
  if (!isLoggedIn) return;

  const messaging = await inicializarFCM();
  if (!messaging) return;

  if (Notification.permission === 'granted') {
    // ✅ Permissão já concedida — gera/atualiza token imediatamente
    await solicitarPermissaoNotificacao(messaging);

  } else if (Notification.permission === 'denied') {
    // ✅ Bloqueado — não tenta pedir, não mostra modal
    console.warn('[FCM] Notificações bloqueadas pelo usuário nas configurações do navegador.');

  } else {
    // permission === 'default' — nunca perguntou ainda
    const jaSolicitouPermissao = localStorage.getItem('notif_permission_asked');
    if (!jaSolicitouPermissao) {
      setTimeout(() => {
        mostrarModalPermissaoNotificacao(messaging);
      }, 5000);
    }
  }
});

// ─────────────────────────────────────────────
// 10. MODAL CUSTOMIZADO PARA PERMISSÃO DE NOTIFICAÇÃO
// ─────────────────────────────────────────────
function mostrarModalPermissaoNotificacao(messaging) {
  if (localStorage.getItem('notif_permission_asked')) return;
  // Nunca mostra se já está bloqueado
  if (Notification.permission === 'denied') return;

  const modal = document.createElement('div');
  modal.id = 'pwa-notif-modal';
  modal.style.cssText = `
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.75);
    z-index: 10000;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    padding: 20px;
    animation: pwaFadeIn 0.3s ease;
  `;
  modal.innerHTML = `
    <style>
      @keyframes pwaFadeIn { from { opacity:0; } to { opacity:1; } }
    </style>
    <div style="background:#0a0a1a; border:1px solid #8b5cf6; border-radius:20px; padding:28px; max-width:400px; width:100%; text-align:center;">
      <div style="font-size:48px; margin-bottom:12px;">🔔</div>
      <h5 style="color:#fff; margin-bottom:8px;">Ativar Notificações</h5>
      <p style="color:#a3a3a3; font-size:14px; margin-bottom:24px; line-height:1.6;">
        Receba alertas de simulados agendados, resultados de redação,
        respostas na HelpZone e lembretes para manter sua sequência de estudos!
      </p>
      <div style="display:flex; flex-direction:column; gap:10px;">
        <button id="btn-ativar-notif" style="background:#8b5cf6; color:white; border:none; border-radius:12px; padding:14px; font-size:15px; font-weight:600; cursor:pointer;">
          ✅ Ativar Notificações
        </button>
        <button id="btn-recusar-notif" style="background:transparent; color:#a3a3a3; border:1px solid #333; border-radius:12px; padding:12px; font-size:14px; cursor:pointer;">
          Agora não
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  localStorage.setItem('notif_permission_asked', 'true');

  document.getElementById('btn-ativar-notif').addEventListener('click', async () => {
    modal.remove();
    await solicitarPermissaoNotificacao(messaging);
  });

  document.getElementById('btn-recusar-notif').addEventListener('click', () => {
    modal.remove();
  });
}

// ─────────────────────────────────────────────
// Expõe funções globalmente (útil para debug no console)
// ─────────────────────────────────────────────
window.launcherPWA = {
  instalarPWA,
  solicitarPermissaoNotificacao,
  mostrarModalPermissaoNotificacao,
  mostrarBotaoInstalacao,
  mostrarAvisoPermissaoBloqueada,
  inicializarFCM,
};
