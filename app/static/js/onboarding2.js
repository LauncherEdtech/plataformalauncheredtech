// app/static/js/onboarding.js
// Sistema de Onboarding - TODOS os modais com opção de pular
// ✅ VERSÃO FINAL - 2026-02-18

class OnboardingManager {
    constructor() {
        this.etapaAtual = null;
        this.dadosEtapa = null;
        this.overlay = null;
        this.modal = null;
        this.highlightedElement = null;
        this.isActive = false;

        // Timers para detecção de ações
        this.aulaTimer = null;
        this.aulaStartTime = null;

        // Locks para evitar múltiplos POSTs
        this._tourCompletoLock = false;
        this._finalizarLock = false;
        this._adiarLock = false;
        
        // Totais de XP/Diamantes
        this._xpTotalGanho = null;
        this._diamantesTotalGanho = null;
        
        // Monitor ativo do diagnóstico
        this._diagnosticoMonitorAtivo = false;
    }

    // Normaliza paths para evitar loops
    normalizePath(path) {
        if (!path) return '/';
        path = String(path).split('?')[0].split('#')[0];
        if (!path.startsWith('/')) path = '/' + path;
        if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
        return path;
    }

    // ==================== INICIALIZAÇÃO ====================
    
    async init() {
        console.log('🎯 Inicializando OnboardingManager...');
        const status = await this.checkStatus();

        if (!status || !status.ativo) {
            console.log('ℹ️ Onboarding não ativo');
            return;
        }

        this.isActive = true;
        this.etapaAtual = status.etapa || null;
        this.dadosEtapa = status.dados_etapa || null;

        console.log('✅ Onboarding ativo detectado', status);

        // Criar elementos do overlay e modal
        this.createOverlay();
        this.createModal();

        await this.showCurrentStep();
    }

    async checkStatus() {
        try {
            console.log('📡 Verificando status do onboarding...');
            const response = await fetch('/api/onboarding/status', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin'
            });
            
            console.log(`📊 Status response: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                console.error(`❌ Erro HTTP: ${response.status}`);
                return null;
            }
            
            const data = await response.json();
            console.log('✅ Status recebido:', data);
            
            // Normaliza formatos possíveis
            const ativo = !!data.ativo || data.status === 'ativo' || data.status === 'basico_completo';
            
            return { ...data, ativo };
        } catch (error) {
            console.error('❌ Erro ao verificar status:', error);
            return null;
        }
    }
    
    // ==================== CRIAÇÃO DE ELEMENTOS ====================
    
    createOverlay() {
        if (this.overlay) return;
        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        document.body.appendChild(this.overlay);
    }
    
    createModal() {
        if (this.modal) return;
        this.modal = document.createElement('div');
        this.modal.className = 'onboarding-modal center';
        document.body.appendChild(this.modal);
    }
    
    // ==================== EXIBIÇÃO DE ETAPAS ====================
    async showCurrentStep() {
        // ✅ Se não veio dados_etapa, tenta reconsultar
        if (!this.dadosEtapa) {
            console.warn('⚠️ Sem dados da etapa - tentando reconsultar status...');
            const status = await this.checkStatus();

            if (status?.dados_etapa) {
                this.etapaAtual = status.etapa;
                this.dadosEtapa = status.dados_etapa;
            } else if (status?.status === 'basico_completo') {
                this.etapaAtual = 5;
                this.dadosEtapa = {
                    nome: 'finalizacao',
                    titulo: '🎊 Parabéns! Tour Básico Completo!',
                    descricao: 'Você já conhece o essencial da plataforma! Quer fazer o tour completo e ganhar 100 Launcher Coins extras?',
                    rota_destino: null,
                    acao_necessaria: 'escolher_proximo_passo',
                    recompensa: { xp: 0, diamantes: 0 },
                    opcoes: [
                        { texto: '🚀 Pular Etapa', acao: 'finalizar_basico' },
                        { texto: '📚 Tour Completo (+100 Launcher Coins)', acao: 'continuar_tour_completo' },
                        { texto: '⏭️ Fazer Depois', acao: 'adiar_tour' }
                    ]
                };
            } else {
                return;
            }
        }

        const currentPath = this.normalizePath(window.location.pathname);
        const destino = this.dadosEtapa?.rota_destino ? this.normalizePath(this.dadosEtapa.rota_destino) : null;
        const isSimuladoIdPage = /^\/simulados\/\d+(\/|$)/.test(currentPath);
        const isQuestaoPage = /\/questao\//.test(currentPath);

        console.log('📍 Mostrando etapa:', this.dadosEtapa.nome, '| path:', currentPath, '| destino:', destino);

        // ✅ CORREÇÃO DO LOOP: Diagnóstico
        if (this.dadosEtapa.nome === 'simulado_diagnostico') {
            if (isSimuladoIdPage) {
                console.log('✅ Já está dentro de /simulados/<id>/... (diagnóstico em andamento), sem redirect');
                if (isQuestaoPage) {
                    this.hideModal();
                    return;
                }
                this.showSimuladoDiagnostico();
                return;
            }
            if (destino && currentPath !== destino) {
                console.log('🔄 Redirecionando para iniciar diagnóstico:', destino);
                window.location.href = destino;
                return;
            }
        }

        // ✅ CORREÇÃO DO LOOP: Redação
        if (this.dadosEtapa.nome === 'redacao') {
            if (currentPath.startsWith('/redacao')) {
                console.log('✅ Já está na Redação, não redirecionar');
                if (currentPath.includes('/nova')) {
                    console.log('🔽 Usuário está escrevendo redação, minimizando modal');
                    this.hideModal();
                    return;
                }
                this.showRedacao();
                return;
            }
            if (destino && currentPath !== destino) {
                window.location.href = destino;
                return;
            }
        }

        // ✅ CORREÇÃO DO LOOP: Shop
        if (this.dadosEtapa.nome === 'shop') {
            if (currentPath.startsWith('/shop')) {
                console.log('✅ Já está no Shop, não redirecionar');
                this.showShop();
                return;
            }
            if (destino && currentPath !== destino) {
                window.location.href = destino;
                return;
            }
        }

        // ✅ CORREÇÃO DO LOOP: HelpZone
        if (this.dadosEtapa.nome === 'helpzone') {
            if (currentPath.startsWith('/helpzone')) {
                console.log('✅ Já está no HelpZone, não redirecionar');
                if (currentPath.includes('/criar-post')) {
                    console.log('🔽 Usuário está criando post, minimizando modal');
                    this.hideModal();
                    return;
                }
                this.showHelpZone();
                return;
            }
            if (destino && currentPath !== destino) {
                console.log('🔄 Redirecionando para HelpZone:', destino);
                window.location.href = destino;
                return;
            }
        }

        // ✅ Outras etapas: redireciona quando destino existe e é diferente
        if (destino && currentPath !== destino) {
            console.log('🔄 Redirecionando para:', destino);
            window.location.href = destino;
            return;
        }

        await this.waitForPageLoad();

        switch (this.dadosEtapa.nome) {
            case 'boas_vindas':
                this.showBoasVindas();
                break;
            case 'cronograma':
                this.showCronograma();
                break;
            case 'primeira_aula':
                this.showPrimeiraAula();
                break;
            case 'simulado_diagnostico':
                this.showSimuladoDiagnostico();
                break;
            case 'finalizacao':
                this.showFinalizacao();
                break;
            case 'helpzone':
                this.showHelpZone();
                break;
            case 'redacao':
                this.showRedacao();
                break;
            case 'shop':
                this.showShop();
                break;
            case 'metricas':
                this.showMetricas();
                break;
            case 'tour_completo_finalizado':
                this.showTourCompletoFinalizado();
                break;
            default:
                console.warn('⚠️ Etapa desconhecida:', this.dadosEtapa.nome);
        }
    }

    // ==================== HELPERS DE CARREGAMENTO ====================

    waitForPageLoad(extraDelayMs = 300) {
        return new Promise((resolve) => {
            const done = () => setTimeout(resolve, extraDelayMs);

            if (document.readyState === 'complete') {
                return done();
            }

            if (document.readyState === 'interactive') {
                return done();
            }

            const onReady = () => {
                window.removeEventListener('load', onReady);
                document.removeEventListener('DOMContentLoaded', onReady);
                done();
            };

            window.addEventListener('load', onReady, { once: true });
            document.addEventListener('DOMContentLoaded', onReady, { once: true });

            setTimeout(() => {
                try {
                    window.removeEventListener('load', onReady);
                    document.removeEventListener('DOMContentLoaded', onReady);
                } catch (_) {}
                done();
            }, 8000);
        });
    }

    // ==================== HELPER: POST JSON ====================

    async postJSON(url, body = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(body)
            });

            const data = await response.json();

            return {
                ok: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            console.error(`❌ Erro em ${url}:`, error);
            return {
                ok: false,
                status: 0,
                data: { erro: error.message }
            };
        }
    }

    // ==================== ETAPAS ESPECÍFICAS ====================
    
    showBoasVindas() {
        const progresso = 0;
        const totalEtapas = 4;
        
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                <div class="onboarding-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${progresso}%"></div>
                    </div>
                    <div class="progress-text">Etapa 1 de ${totalEtapas}</div>
                </div>
                
                <div class="onboarding-actions">
                    <button class="onboarding-btn onboarding-btn-secondary" onclick="onboardingManager.skip()">
                        ⏭️ Fazer Depois
                    </button>
                    <button class="onboarding-btn onboarding-btn-primary" onclick="onboardingManager.startTour()">
                        🚀 Começar Tour
                    </button>
                </div>
            </div>
        `;
        
        this.showModal();
    }
    
    showCronograma() {
        const progresso = 25;
        const totalEtapas = 4;
        
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                <div class="onboarding-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${progresso}%"></div>
                    </div>
                    <div class="progress-text">Etapa 1 de ${totalEtapas}</div>
                </div>
                
                <div class="onboarding-reward">   
                    <div class="reward-icon">🪙</div>
                    <div class="reward-text">
                        <div class="reward-title">Recompensa</div>
                        <div class="reward-value">
                            +${this.dadosEtapa.recompensa.xp} XP • 
                            +${this.dadosEtapa.recompensa.diamantes} <span class="launcher-coin-icon"></span>
                        </div>
                    </div>
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 15px;">
                    👇 Preencha o formulário abaixo para criar seu cronograma
                </p>
                
                <div class="onboarding-actions">
                    <button class="onboarding-btn onboarding-btn-secondary" onclick="onboardingManager.pularEtapaAtual()">
                        ⏭️ Pular Etapa
                    </button>
                    <button class="onboarding-btn onboarding-btn-primary" onclick="onboardingManager.hideTemporarily()">
                        📝 Preencher Formulário
                    </button>
                </div>
            </div>
        `;
        
        this.showModal();
        
        if (this.dadosEtapa.elemento_destaque) {
            this.highlightElement(this.dadosEtapa.elemento_destaque);
        }
        
        this.monitorCronogramaCriacao();
    }

    showPrimeiraAula() {
        const progresso = 50;
        const totalEtapas = 4;
        
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                ${this.dadosEtapa.info_adicional ? `
                    <div class="onboarding-info">
                        ${this.dadosEtapa.info_adicional}
                    </div>
                ` : ''}
                
                <div class="onboarding-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${progresso}%"></div>
                    </div>
                    <div class="progress-text">Etapa 2 de ${totalEtapas}</div>
                </div>
                
                <div class="onboarding-reward">
                    <div class="reward-icon">🪙</div>
                    <div class="reward-text">
                        <div class="reward-title">Recompensa</div>
                        <div class="reward-value">
                            +${this.dadosEtapa.recompensa.xp} XP •
                            +${this.dadosEtapa.recompensa.diamantes} <span class="launcher-coin-icon"></span>
                         </div>
                    </div>
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 15px;">
                    👇 Assista 2 minutos da aula abaixo para ganhar sua recompensa
                </p>

                <div class="onboarding-actions">
                    <button class="onboarding-btn onboarding-btn-secondary" onclick="onboardingManager.pularEtapaAtual()">
                        ⏭️ Pular Etapa
                    </button>
                    <button class="onboarding-btn onboarding-btn-primary" onclick="onboardingManager.hideTemporarily()">
                        🎥 Assistir Aula
                    </button>
                </div>
            </div>
        `;

        this.showModal();
        
        if (this.dadosEtapa.elemento_destaque) {
            this.highlightElement(this.dadosEtapa.elemento_destaque);
        }
        
        this.monitorAulaInicio();
    }
    
    showSimuladoDiagnostico() {
        const progresso = 75;
        const totalEtapas = 4;

        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>

                ${this.dadosEtapa.info_adicional ? `
                    <div class="onboarding-info">
                        ${this.dadosEtapa.info_adicional}
                    </div>
                ` : ''}

                <div class="onboarding-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${progresso}%"></div>
                    </div>
                    <div class="progress-text">Etapa 3 de ${totalEtapas}</div>
                </div>

                <div class="onboarding-reward">
                    <div class="reward-icon">🪙</div>
                    <div class="reward-text">
                        <div class="reward-title">Recompensa</div>
                        <div class="reward-value">
                            +${this.dadosEtapa.recompensa.xp} XP •
                            +${this.dadosEtapa.recompensa.diamantes} <span class="launcher-coin-icon"></span>
                         </div>
                    </div>
                </div>

                <div class="onboarding-actions">
                    <button class="onboarding-btn onboarding-btn-secondary" onclick="onboardingManager.pularEtapaAtual()">
                        ⏭️ Pular Etapa
                    </button>
                    <button class="onboarding-btn onboarding-btn-primary"
                            onclick="window.location.href='${this.dadosEtapa.rota_destino || "/simulados/diagnostico-onboarding"}'">
                        📊 Iniciar Diagnóstico
                    </button>
                </div>
            </div>
        `;

        this.showModal();
        this.monitorDiagnosticoConclusao();
    }

    showFinalizacao() {
        const xpTotal = this._xpTotalGanho ?? 100;
        const diamantesTotal = this._diamantesTotalGanho ?? 50;

        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <div class="onboarding-summary">
                    <div class="summary-title">🎊 Você Completou o Tour Básico!</div>
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <span class="summary-stat-value">${xpTotal}</span>
                            <span class="summary-stat-label">XP Ganho</span>
                        </div>
                        <div class="summary-stat">
                            <span class="summary-stat-value">${diamantesTotal}</span>
                            <span class="summary-stat-label"><span class="launcher-coin-icon"></span> Launcher Coins</span>
                        </div>
                    </div>
                </div>

                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>

                <div class="onboarding-actions" style="flex-direction: column; gap: 12px;">
                    <button type="button"
                            class="onboarding-btn onboarding-btn-primary"
                            onclick="window.onboardingManager.iniciarTourCompleto()">
                        📚 Tour Completo (+100 <span class="launcher-coin-icon"></span>)
                    </button>

                    <button type="button"
                            class="onboarding-btn onboarding-btn-secondary"
                            onclick="window.onboardingManager.finalizarBasico()">
                        ⏭️ Pular Etapa
                    </button>

                    <button type="button"
                            class="onboarding-btn onboarding-btn-danger"
                            onclick="window.onboardingManager.adiarTour()">
                        ⏸️ Fazer Depois
                    </button>
                </div>
            </div>
        `;

        this.showModal();
    }

    // ==================== ETAPAS DO TOUR COMPLETO ====================

    showHelpZone() {
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                ${this.dadosEtapa.info_adicional ? `
                    <div class="onboarding-info">
                        ${this.dadosEtapa.info_adicional}
                    </div>
                ` : ''}
                
                <div class="onboarding-reward">
                    <div class="reward-icon">🪙</div>                    
                    <div class="reward-text">
                        <div class="reward-title">Recompensa</div>
                        <div class="reward-value">
                            +${this.dadosEtapa.recompensa.xp} XP • 
                            +${this.dadosEtapa.recompensa.diamantes} <span class="launcher-coin-icon"></span>
                        </div>
                    </div>
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 15px;">
                    👇 Crie seu primeiro post no HelpZone para avançar
                </p>
                
                <div class="onboarding-actions">
                    <button class="onboarding-btn onboarding-btn-secondary" 
                            onclick="onboardingManager.pularEtapaAtual()">
                        ⏭️ Pular Etapa
                    </button>
                    <button class="onboarding-btn onboarding-btn-primary" 
                            onclick="window.location.href='/helpzone/criar-post'">
                        ✍️ Criar Primeiro Post
                    </button>
                </div>
            </div>
        `;
        
        this.showModal();
        
        if (this.dadosEtapa.elemento_destaque) {
            this.highlightElement(this.dadosEtapa.elemento_destaque);
        }
    }

    showRedacao() {
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                ${this.dadosEtapa.info_adicional ? `
                    <div class="onboarding-info">
                        ${this.dadosEtapa.info_adicional}
                    </div>
                ` : ''}
                
                <div class="onboarding-reward">
                    <div class="reward-icon">🪙</div>
                    <div class="reward-text">
                        <div class="reward-title">Recompensa por enviar</div>
                        <div class="reward-value">
                            +${this.dadosEtapa.recompensa.xp} XP •
                            +${this.dadosEtapa.recompensa.diamantes} <span class="launcher-coin-icon"></span>
                        </div>
                    </div>
                </div>
                
                <div class="onboarding-actions" style="flex-direction: column; gap: 10px;">
                    <button class="onboarding-btn onboarding-btn-primary" 
                            onclick="window.location.href='/redacao/nova'">
                        ✍️ Enviar Redação Agora
                    </button>
                    <button class="onboarding-btn onboarding-btn-secondary" 
                            onclick="onboardingManager.avancarEtapa('enviar_redacao')">
                        ⏭️ Pular Esta Etapa
                    </button>
                </div>
            </div>
        `;
        
        this.showModal();
    }

    showShop() {
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                ${this.dadosEtapa.info_adicional ? `
                    <div class="onboarding-info">
                        ${this.dadosEtapa.info_adicional}
                    </div>
                ` : ''}
                
                <div class="onboarding-actions" style="flex-direction: column; gap: 10px;">
                    <button class="onboarding-btn onboarding-btn-primary" 
                            onclick="onboardingManager.hideModal(); window.scrollTo(0,0);">
                        🛍️ Ver Produto Especial
                    </button>
                    <button class="onboarding-btn onboarding-btn-secondary" 
                            onclick="onboardingManager.pularEtapaAtual()">
                        ⏭️ Pular Etapa
                    </button>
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 0.85rem; margin-top: 12px;">
                    👆 Feche este modal e clique em "Desbloquear Agora" no produto
                </p>
            </div>
        `;
        
        this.showModal();
    }

    showMetricas() {
        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>
                
                ${this.dadosEtapa.info_adicional ? `
                    <div class="onboarding-info">
                        ${this.dadosEtapa.info_adicional}
                    </div>
                ` : ''}
                
                <div class="onboarding-actions" style="flex-direction: column; gap: 10px;">
                    <button id="btn-avancar-metricas"
                            class="onboarding-btn onboarding-btn-primary" 
                            onclick="onboardingManager.avancarEtapa('visualizar_metricas')"
                            disabled
                            style="opacity: 0.5; cursor: not-allowed;">
                        ✅ Continuar <span id="timer-metricas">(10s)</span>
                    </button>
                    <button class="onboarding-btn onboarding-btn-secondary" 
                            onclick="onboardingManager.pularEtapaAtual()">
                        ⏭️ Pular Etapa
                    </button>
                </div>
            </div>
        `;
        
        this.showModal();
        
        if (this.dadosEtapa.elemento_destaque) {
            this.highlightElement(this.dadosEtapa.elemento_destaque);
        }
        
        let segundos = 10;
        const timerEl = document.getElementById('timer-metricas');
        const btnEl = document.getElementById('btn-avancar-metricas');
        
        const interval = setInterval(() => {
            segundos--;
            if (timerEl) timerEl.textContent = `(${segundos}s)`;
            if (segundos <= 0) {
                clearInterval(interval);
                if (btnEl) {
                    btnEl.disabled = false;
                    btnEl.style.opacity = '1';
                    btnEl.style.cursor = 'pointer';
                    if (timerEl) timerEl.textContent = '';
                }
            }
        }, 1000);
    }

    showTourCompletoFinalizado() {
        const xpTotal = this._xpTotalGanho || 300;
        const diamantesTotal = this._diamantesTotalGanho || 150;


        this.modal.innerHTML = `
            <div class="onboarding-header">
                <h2 class="onboarding-title">
                    ${this.dadosEtapa.titulo}
                </h2>
            </div>
            <div class="onboarding-body">
                <div class="onboarding-summary">
                    <div class="summary-title">🏆 Tour Completo Finalizado!</div>
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <span class="summary-stat-value">${xpTotal}</span>
                            <span class="summary-stat-label">XP Total</span>
                        </div>
                        <div class="summary-stat">
                            <span class="summary-stat-value">${diamantesTotal}</span>
                            <span class="summary-stat-label"><span class="launcher-coin-icon"></span> Launcher Coins</span>
                        </div>
                    </div>
                </div>
                
                <p class="onboarding-description">
                    ${this.dadosEtapa.descricao}
                </p>

                <div class="onboarding-actions">
                    <button class="onboarding-btn onboarding-btn-primary" 
                            onclick="onboardingManager.finalizarTourCompleto()">
                        🚀 Começar a Estudar!
                    </button>
                </div>
            </div>
        `;
        
        this.showModal();
    }
    
    // ==================== AÇÕES ====================

    async startTour() {
        console.log('🚀 Iniciando tour...');
        await this.advanceStep('aceitar_tour');
    }
    
    async skip() {
        if (confirm('Tem certeza que deseja pular o tour? Você pode fazer depois a qualquer momento.')) {
            await fetch('/api/onboarding/pular', { method: 'POST' });
            this.hideModal();
            this.isActive = false;
        }
    }

    // ✅ NOVA FUNÇÃO: Pular etapa atual
    async pularEtapaAtual() {
        try {
            console.log('⏭️ Pulando etapa atual...');
            
            // Mapeamento de nome de etapa para ação correspondente
            const acoesPorEtapa = {
                'cronograma': 'criar_cronograma',
                'primeira_aula': 'assistir_aula',
                'simulado_diagnostico': 'concluir_diagnostico',
                'helpzone': 'criar_post',
                'redacao': 'enviar_redacao',
                'shop': 'desbloquear_produto',
                'metricas': 'visualizar_metricas'
            };
            
            const acao = acoesPorEtapa[this.dadosEtapa.nome];
            
            if (!acao) {
                console.warn('⚠️ Ação não mapeada para:', this.dadosEtapa.nome);
                return;
            }
            
            await this.avancarEtapa(acao);
            
        } catch (e) {
            console.error('❌ Erro ao pular etapa:', e);
        }
    }

    async finalizarBasico() {
        if (this._finalizarLock) return;
        this._finalizarLock = true;

        try {
            const { ok } = await this.postJSON('/api/onboarding/finalizar-permanente', {});
            
            if (!ok) {
                alert('Erro ao finalizar onboarding.');
                this._finalizarLock = false;
                return;
            }

            this.isActive = false;
            this.hideModal();
            window.location.href = '/dashboard';
        } catch (e) {
            console.error('❌ Erro ao finalizar básico:', e);
            this._finalizarLock = false;
        }
    }

    async adiarTour() {
        if (this._adiarLock) return;
        this._adiarLock = true;

        try {
            const { ok } = await this.postJSON('/api/onboarding/pular', {});
            
            if (!ok) {
                alert('Erro ao adiar tour.');
                this._adiarLock = false;
                return;
            }

            this.isActive = false;
            this.hideModal();
        } catch (e) {
            console.error('❌ Erro ao adiar tour:', e);
            this._adiarLock = false;
        }
    }

    async iniciarTourCompleto() {
        if (this._tourCompletoLock) {
            console.warn('⚠️ Aguarde, processando tour completo...');
            return;
        }
        
        this._tourCompletoLock = true;

        const allButtons = document.querySelectorAll('.onboarding-actions button');
        allButtons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        });

        try {
            console.log('📚 Iniciando tour completo...');

            const { ok, status, data } = await this.postJSON('/api/onboarding/ativar-tour-completo', {});

            if (!ok) {
                console.error('❌ Erro ao ativar tour completo:', status, data);
                alert(`Erro ao iniciar tour completo: ${data?.mensagem || 'Erro desconhecido'}`);
                
                allButtons.forEach(btn => {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                });
                
                this._tourCompletoLock = false;
                return;
            }

            console.log('✅ Tour completo ativado:', data);

            this.etapaAtual = data?.etapa || 6;
            this.dadosEtapa = data?.dados_etapa || null;

            this.hideModal();

            setTimeout(() => {
                this.showCurrentStep();
            }, 500);

        } catch (e) {
            console.error('❌ Erro ao iniciar tour completo:', e);
            alert('Erro ao iniciar tour completo. Tente novamente.');
            
            allButtons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            });
        } finally {
            setTimeout(() => {
                this._tourCompletoLock = false;
            }, 2000);
        }
    }

    async advanceStep(acao) {
        try {
            const response = await fetch('/api/onboarding/avancar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ acao })
            });
            
            const data = await response.json();
            console.log('➡️ Avançando etapa:', data);
            
            if (data.status === 'ativo') {
                this.dadosEtapa = data.dados_etapa;
                this.etapaAtual = data.etapa;
                
                if (data.recompensa) {
                    await this.showReward(data.recompensa);
                }
                
                this.hideModal();
                setTimeout(() => this.showCurrentStep(), 500);
            } else if (data.status === 'basico_finalizado') {
                this.dadosEtapa = data.dados_etapa;
                this.showCurrentStep();
            }
            
        } catch (error) {
            console.error('❌ Erro ao avançar etapa:', error);
        }
    }

    async avancarEtapa(acao) {
        try {
            console.log(`➡️ Avançando etapa: ${acao}`);
            
            const { ok, data } = await this.postJSON('/api/onboarding/avancar', { acao });
            
            if (!ok) {
                console.error('❌ Erro ao avançar etapa:', data);
                return;
            }
            
            console.log('✅ Etapa avançada:', data);
            
            if (data.recompensa) {
                await this.showReward(data.recompensa);
            }
            
            this.etapaAtual = data.etapa;
            this.dadosEtapa = data.dados_etapa;
            
            this.hideModal();
            
            setTimeout(() => {
                this.showCurrentStep();
            }, 500);
            
        } catch (error) {
            console.error('❌ Erro ao avançar etapa:', error);
        }
    }

    async finalizarTourCompleto() {
        try {
            const { ok } = await this.postJSON('/api/onboarding/avancar', { 
                acao: 'finalizar_tour_completo' 
            });
            
            if (!ok) {
                alert('Erro ao finalizar tour completo.');
                return;
            }
            
            this.isActive = false;
            this.hideModal();
            window.location.href = '/dashboard';
            
        } catch (e) {
            console.error('❌ Erro ao finalizar tour completo:', e);
        }
    }
    
    // ==================== MONITORES DE AÇÕES ====================
    
    monitorCronogramaCriacao() {
        const checkForm = setInterval(() => {
            const form = document.querySelector('#wizard-form') || document.querySelector('form[action*="cronograma"]');
            
            if (form) {
                console.log('📝 Formulário de cronograma encontrado');
                clearInterval(checkForm);
                
                form.addEventListener('submit', async (e) => {
                    console.log('✅ Cronograma sendo criado...');
                    setTimeout(async () => {
                        await fetch('/api/onboarding/detectar/cronograma-criado', { method: 'POST' });
                    }, 2000);
                });
            }
        }, 500);
        
        setTimeout(() => clearInterval(checkForm), 30000);
    }
    
    monitorAulaInicio() {
        console.log('🔍 Iniciando monitoramento de aula...');
        
        let checkCount = 0;
        const checkAula = setInterval(() => {
            checkCount++;
            console.log(`🔎 Tentativa ${checkCount}: Procurando player...`);
            
            const youtubeIframe = document.querySelector('iframe[src*="youtube"]');
            const videoElement = document.querySelector('video');
            
            console.log('📺 YouTube:', youtubeIframe ? 'ENCONTRADO' : 'NÃO ENCONTRADO');
            console.log('📺 Video:', videoElement ? 'ENCONTRADO' : 'NÃO ENCONTRADO');
            
            const videoFound = youtubeIframe || videoElement;
            
            if (videoFound && !this.aulaTimer) {
                console.log('🎥 ✅ VÍDEO ENCONTRADO! Iniciando timer...');
                this.aulaStartTime = Date.now();
                
                this.aulaTimer = setInterval(() => {
                    const tempoAssistido = (Date.now() - this.aulaStartTime) / 1000;
                    console.log(`⏱️ Tempo: ${Math.floor(tempoAssistido)}s / 120s`);
                    
                    if (tempoAssistido >= 120) {
                        console.log('✅ 2 minutos completados!');
                        clearInterval(this.aulaTimer);
                        
                        fetch('/api/onboarding/detectar/aula-assistida', { method: 'POST' })
                            .then(r => r.json())
                            .then(data => console.log('📡 Resposta API:', data))
                            .catch(err => console.error('❌ Erro API:', err));
                    }
                }, 1000);
                
                clearInterval(checkAula);
            }
        }, 1000);
        
        setTimeout(() => {
            clearInterval(checkAula);
            console.log('⏰ Timeout 60s atingido');
        }, 60000);
    }

    monitorDiagnosticoConclusao() {
        if (this._diagnosticoMonitorAtivo) return;
        this._diagnosticoMonitorAtivo = true;

        const checkResultado = setInterval(async () => {
            const resultadoElement =
                document.querySelector('.diagnostico-resultado') ||
                document.querySelector('[data-diagnostico-concluido]');

            if (!resultadoElement) return;

            console.log('✅ Diagnóstico concluído!');
            clearInterval(checkResultado);

            try {
                const resp = await fetch('/api/onboarding/detectar/diagnostico-concluido', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!resp.ok) {
                    console.error('❌ Erro ao notificar diagnóstico concluído:', resp.status);
                    return;
                }

                const data = await resp.json();
                console.log('📡 Resposta onboarding (diagnóstico concluído):', data);

                if (data?.dados_etapa) {
                    this.etapaAtual = data.etapa ?? this.etapaAtual;
                    this.dadosEtapa = data.dados_etapa;
                    this._xpTotalGanho = data.xp_total_ganho ?? this._xpTotalGanho;
                    this._diamantesTotalGanho = data.diamantes_total_ganho ?? this._diamantesTotalGanho;
                    this.showCurrentStep();
                    return;
                }

                if (data?.status === 'basico_completo' || data?.status === 'basico_finalizado') {
                    this.etapaAtual = 5;
                    this.dadosEtapa = {
                        nome: 'finalizacao',
                        titulo: '🎊 Parabéns! Tour Básico Completo!',
                        descricao: 'Você já conhece o essencial da plataforma! Quer fazer o tour completo e ganhar 100 Launcher Coins extras?',
                        rota_destino: null,
                        acao_necessaria: 'escolher_proximo_passo',
                        recompensa: { xp: 0, diamantes: 0 },
                        opcoes: [
                            { texto: '⏭️ Pular Etapa', acao: 'finalizar_basico' },
                            { texto: '📚 Tour Completo (+100 Launcher Coins)', acao: 'continuar_tour_completo' },
                            { texto: '⏸️ Fazer Depois', acao: 'adiar_tour' }
                        ]
                    };
                    this._xpTotalGanho = data.xp_total_ganho ?? this._xpTotalGanho;
                    this._diamantesTotalGanho = data.diamantes_total_ganho ?? this._diamantesTotalGanho;
                    this.showCurrentStep();
                }

            } catch (err) {
                console.error('❌ Falha ao concluir diagnóstico onboarding:', err);
            }
        }, 1000);

        setTimeout(() => {
            clearInterval(checkResultado);
            this._diagnosticoMonitorAtivo = false;
        }, 600000);
    }
    
    // ==================== UI HELPERS ====================
    
    showModal() {
        if (!this.overlay) this.createOverlay();
        if (!this.modal) this.createModal();
        this.overlay.classList.add('active');
        this.modal.classList.add('active');
    }


    hideModal() {
        try {
            if (this.modal) {
                this.modal.classList.remove('active');
            }
            if (this.overlay) {
                this.overlay.classList.remove('active');
            }
            this.removeHighlight();
        } catch (e) {
            console.warn('hideModal error', e);
        }
    }
    
    hideTemporarily() {
        console.log('⏸️ Minimizando modal temporariamente');
        this.hideModal();
    }
    
    highlightElement(selector) {
        let attempts = 0;
        const maxAttempts = 10;
        
        const tryHighlight = setInterval(() => {
            const element = document.querySelector(selector);
            
            if (element) {
                console.log('🎯 Elemento destacado:', selector);
                this.highlightedElement = element;
                element.classList.add('onboarding-highlight');
                clearInterval(tryHighlight);
            }
            
            attempts++;
            if (attempts >= maxAttempts) {
                console.warn('⚠️ Elemento não encontrado:', selector);
                clearInterval(tryHighlight);
            }
        }, 500);
    }
    
    removeHighlight() {
        if (this.highlightedElement) {
            this.highlightedElement.classList.remove('onboarding-highlight');
            this.highlightedElement = null;
        }
        const existing = document.getElementById('onboarding-highlight-style');
        if (existing) existing.remove();
    }
    
    async showReward(recompensa) {
        return new Promise(resolve => {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10001;
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border: 2px solid #f59e0b;
                border-radius: 12px;
                padding: 15px 20px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                animation: slideInFromRight 0.5s ease;
            `;

            toast.innerHTML = `
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 2rem;">🎉</span>
                    <div>
                        <div style="font-weight: 700; color: #92400e;">Recompensa Ganha!</div>
                        <div style="color: #b45309; font-size: 0.9rem;">
                            ${recompensa.xp > 0 ? `+${recompensa.xp} XP` : ''} 
                            ${recompensa.diamantes > 0 ? `+${recompensa.diamantes} <span class="launcher-coin-icon"></span>` : ''}
                            ${recompensa.badge ? `<br>🏆 ${recompensa.badge}` : ''}
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideOutToRight 0.5s ease';
                setTimeout(() => {
                    toast.remove();
                    resolve();
                }, 500);
            }, 3000);
        });
    }
}

// ==================== INICIALIZAÇÃO GLOBAL ====================

if (!window.__onboardingInitialized) {
    window.__onboardingInitialized = true;
    window.onboardingManager = null;

    document.addEventListener('DOMContentLoaded', () => {
        if (window.onboardingManager) return;
        window.onboardingManager = new OnboardingManager();
        window.onboardingManager.init();
    });

    const styleId = 'onboarding-animations-style';
    let onboardingAnimationStyle = document.getElementById(styleId);

    if (!onboardingAnimationStyle) {
        onboardingAnimationStyle = document.createElement('style');
        onboardingAnimationStyle.id = styleId;
        onboardingAnimationStyle.textContent = `
            @keyframes slideInFromRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }

            @keyframes slideOutToRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(onboardingAnimationStyle);
    }
}
