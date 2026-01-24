// ============================================================
// app/static/js/freemium-handler.js
// Handler principal do sistema freemium da Plataforma Launcher
// Versão estável 2025-11 — elimina loops e travamentos
// ============================================================

(function() {
  console.log("🚀 Freemium Handler iniciado");

  // Evitar inicializações duplicadas
  if (window.__freemiumHandlerInitialized) {
    console.warn("⚠️ FreemiumHandler já foi inicializado, ignorando duplicação.");
    return;
  }
  window.__freemiumHandlerInitialized = true;

  // Flag global de bloqueio para evitar múltiplas requisições simultâneas
  let bloqueado = false;

  // ===============================================
  // 🔍 Função para consultar o backend via API Flask
  // ===============================================
  async function verificarLimite(tipo) {
    try {
      console.log(`🔎 Verificando limite freemium: ${tipo}`);
      const resp = await fetch(`/api/freemium/verificar/${tipo}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });

      const data = await resp.json();
      console.log("📊 Resposta da API freemium:", data);

      // Se pode acessar normalmente
      if (data.success && data.pode_acessar) {
        return true;
      }

      // Caso bloqueado — exibir modal
      if (data.mostrar_modal || data.success === true && data.pode_acessar === false) {
        console.log(`🔒 Limite atingido (${tipo}) — exibindo modal freemium`);
        if (typeof window.showFreemiumModal === "function") {
          window.showFreemiumModal(tipo);
        } else {
          alert(data.mensagem || "Você atingiu o limite gratuito. Assine para continuar!");
        }
      }

      return false;
    } catch (error) {
      console.error("❌ Erro ao verificar limite freemium:", error);
      return false;
    }
  }

  // =====================================================
  // 🔗 Interceptador de cliques (aulas, simulados, redações)
  // =====================================================
  function interceptar(tipo, seletor) {
    const links = document.querySelectorAll(seletor);

    console.log(`🎯 Interceptando ${links.length} links para tipo: ${tipo}`);

    links.forEach(link => {
      // Evita vincular o evento mais de uma vez
      if (link.dataset.freemiumBound) return;
      link.dataset.freemiumBound = "true";

      link.addEventListener("click", async function(e) {
        const href = link.getAttribute("href");
        if (!href || href.startsWith("#")) return;

        // Bloqueio temporário para evitar múltiplos fetch seguidos
        if (bloqueado) {
          e.preventDefault();
          console.log("⏳ Clique bloqueado temporariamente para evitar múltiplas chamadas.");
          return;
        }

        e.preventDefault();
        bloqueado = true;

        const permitido = await verificarLimite(tipo);
        if (permitido) {
          console.log(`✅ Acesso liberado: ${href}`);
          window.location.href = href;
        } else {
          console.log(`🚫 Acesso bloqueado (${tipo}) — modal exibido.`);
        }

        // Libera novamente após 3 segundos
        setTimeout(() => (bloqueado = false), 3000);
      });
    });
  }

  // =====================================================
  // 🧩 Inicialização segura — executa uma única vez
  // =====================================================
  function initFreemiumHandler() {
    console.log("⚙️ Inicializando interceptadores freemium...");

    // Interceptar cliques de cada tipo de conteúdo
    interceptar("aula", "a[href*='/aula/'], a[href*='/modulo/'], a[href*='/estudo/aula/']");
    interceptar("simulado", "a[href*='/simulados/'], a[href*='/simulado']");
    interceptar("redacao", "a[href*='/redacao/'], a[href*='/redacao/nova']");

    // Detectar flash messages carregadas no HTML (fallback)
    detectarFlashMessages();

    // Detectar parâmetro ?show_modal= no URL
    checkUrlParams();

    console.log("✅ FreemiumHandler inicializado (sem loops, sem observer).");
  }

  // =====================================================
  // 🧠 Funções auxiliares
  // =====================================================
  function detectarFlashMessages() {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
      const text = alert.textContent.toLowerCase();
      let tipo = null;
      if (text.includes("aulas gratuitas")) tipo = "aula";
      if (text.includes("simulados gratuitos")) tipo = "simulado";
      if (text.includes("redações gratuitas")) tipo = "redacao";

      if (tipo) {
        console.log(`⚠️ Flash detectado (${tipo}) — exibindo modal.`);
        if (typeof window.showFreemiumModal === "function") {
          window.showFreemiumModal(tipo);
        }
        alert.remove();
      }
    });
  }

  function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const showModal = urlParams.get("show_modal");
    if (showModal) {
      console.log(`🎯 URL contém show_modal=${showModal} — exibindo modal freemium.`);
      if (typeof window.showFreemiumModal === "function") {
        window.showFreemiumModal(showModal);
      }
      const newUrl = window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    }
  }

  // =====================================================
  // 🚀 Execução automática no carregamento da página
  // =====================================================
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFreemiumHandler);
  } else {
    initFreemiumHandler();
  }

})();
