// CAMINHO: app/static/firebase-messaging-sw.js
// ⚠️  O FCM exige este arquivo EXATAMENTE com este nome
//     Também precisa ser servido da raiz: /firebase-messaging-sw.js
//     Veja a rota em: app/routes/pwa.py

importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// ⚠️  SUBSTITUA pelos seus valores do Firebase Console
const firebaseConfig = {

  apiKey: "AIzaSyDsymFEW3dOAZIktTqq1aBl1A3ieqmqc_8",
  authDomain: "launcher-educacao.firebaseapp.com",
  projectId: "launcher-educacao",
  storageBucket: "launcher-educacao.firebasestorage.app",
  messagingSenderId: "411831431678",
  appId: "1:411831431678:web:e648587d06a165c79190af",

};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Lida com mensagens recebidas em background (app fechado/minimizado)
messaging.onBackgroundMessage((payload) => {
  console.log('[FCM-SW] Mensagem em background recebida:', payload);

  const notificationTitle = payload.notification?.title || 'Launcher Educação';
  const notificationOptions = {
    body: payload.notification?.body || 'Você tem uma nova notificação!',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/icon-72x72.png',
    data: {
      url: payload.data?.url || '/dashboard',
    },
    tag: payload.data?.tag || 'fcm-notification',
    vibrate: [200, 100, 200],
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
