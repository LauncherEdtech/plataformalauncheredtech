// static/js/activity_tracker.js - ARQUIVO NOVO A SER CRIADO

class ActivityTracker {
    constructor(atividade) {
        this.atividade = atividade;
        this.isActive = false;
        this.sessionId = null;
        this.ultimaAtividade = Date.now();
        this.tempoMinimoParaXP = 180000; // 3 minutos em ms
        this.intervaloInatividade = 60000; // 1 minuto sem atividade = pausar
        this.intervaloVerificacao = 30000; // Verificar a cada 30 segundos
        
        this.ultimoXpConcedido = Date.now();
        
        this.iniciarMonitoramento();
    }

    iniciarMonitoramento() {
        console.log(`🎯 Iniciando monitoramento rigoroso para: ${this.atividade}`);
        
        // Eventos que indicam atividade real
        const atividades = ['mousedown', 'keydown', 'input', 'change', 'click', 'focus'];
        atividades.forEach(evento => {
            document.addEventListener(evento, () => this.registrarAtividade(), { passive: true });
        });

        // Detectar mudanças de visibilidade
        document.addEventListener('visibilitychange', () => this.gerenciarVisibilidade());
        window.addEventListener('focus', () => this.gerenciarFoco(true));
        window.addEventListener('blur', () => this.gerenciarFoco(false));

        // Monitoramento contínuo
        this.intervalId = setInterval(() => this.verificarStatus(), this.intervaloVerificacao);
        
        // Finalizar ao sair
        window.addEventListener('beforeunload', () => this.finalizarSessao());
        window.addEventListener('pagehide', () => this.finalizarSessao());
    }

    registrarAtividade() {
        this.ultimaAtividade = Date.now();
        
        if (!this.isActive && !document.hidden) {
            this.iniciarSessao();
        }
    }

    async iniciarSessao() {
        if (this.isActive) return;
        
        console.log(`▶️ INICIANDO sessão de XP: ${this.atividade}`);
        
        try {
            const response = await fetch('/api/xp/iniciar-sessao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ atividade: this.atividade })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.isActive = true;
                this.sessionId = data.session_id;
                this.ultimoXpConcedido = Date.now();
                this.mostrarIndicadorXP();
                console.log(`✅ Sessão XP iniciada: ${this.sessionId}`);
            }
        } catch (error) {
            console.error('❌ Erro ao iniciar sessão XP:', error);
        }
    }

    async verificarConcessaoXP(agora) {
        const tempoDesdeUltimoXP = agora - this.ultimoXpConcedido;
        
        if (tempoDesdeUltimoXP >= this.tempoMinimoParaXP) {
            try {
                const response = await fetch('/api/xp/conceder-xp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        session_id: this.sessionId,
                        minutos_ativos: 3 
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.ultimoXpConcedido = agora;
                    this.atualizarWidgetProgresso(data.xp_total, data.diamantes_total);
                    this.mostrarNotificacaoXP(data.xp_ganho, data.diamantes_ganhos);
                    console.log(`🎁 +${data.xp_ganho} XP concedido!`);
                }
            } catch (error) {
                console.error('Erro ao conceder XP:', error);
            }
        }
    }

    verificarStatus() {
        const agora = Date.now();
        const tempoSemAtividade = agora - this.ultimaAtividade;
        
        if (this.isActive && tempoSemAtividade > this.intervaloInatividade) {
            console.log(`⏸️ Pausando por inatividade`);
            this.pausarSessao();
            return;
        }
        
        if (this.isActive && !document.hidden) {
            this.verificarConcessaoXP(agora);
        }
    }

    gerenciarVisibilidade() {
        if (document.hidden) {
            this.pausarSessao();
        } else {
            this.registrarAtividade();
        }
    }

    gerenciarFoco(temFoco) {
        if (!temFoco) {
            this.pausarSessao();
        } else {
            this.registrarAtividade();
        }
    }

    pausarSessao() {
        if (!this.isActive) return;
        
        this.isActive = false;
        this.esconderIndicadorXP();
        
        if (this.sessionId) {
            fetch('/api/xp/pausar-sessao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            }).catch(e => console.error('Erro ao pausar:', e));
        }
    }

    async finalizarSessao() {
        if (!this.isActive || !this.sessionId) return;
        
        const data = { session_id: this.sessionId };
        
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/xp/finalizar-sessao', JSON.stringify(data));
        } else {
            fetch('/api/xp/finalizar-sessao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                keepalive: true
            }).catch(e => console.error('Erro ao finalizar:', e));
        }
        
        this.resetarEstado();
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    mostrarIndicadorXP() {
        let indicador = document.getElementById('xp-progress-indicator');
        if (indicador) {
            indicador.style.display = 'block';
            indicador.querySelector('#xp-activity-text').textContent = `Ganhando XP - ${this.atividade}`;
        }
    }

    esconderIndicadorXP() {
        let indicador = document.getElementById('xp-progress-indicator');
        if (indicador) {
            indicador.style.display = 'none';
        }
    }

    atualizarWidgetProgresso(xpTotal, diamantesTotal) {
        const xpDisplay = document.getElementById('xp-display');
        const diamantsDisplay = document.getElementById('diamonds-display');
        
        if (xpDisplay) xpDisplay.textContent = xpTotal;
        if (diamantsDisplay) diamantsDisplay.textContent = diamantesTotal;
    }

    mostrarNotificacaoXP(xp, diamantes) {
        const notif = document.createElement('div');
        notif.style.cssText = `
            position: fixed; top: 80px; right: 20px; z-index: 9999; 
            background: linear-gradient(135deg, #28a745, #20c997); 
            color: white; padding: 12px 20px; border-radius: 8px; 
            font-weight: 600; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            animation: slideInRight 0.3s ease;
        `;
        notif.innerHTML = `<i class="bi bi-plus-circle"></i> +${xp} XP • +${diamantes} 💎`;
        document.body.appendChild(notif);
        setTimeout(() => notif.remove(), 3000);
    }

    resetarEstado() {
        this.isActive = false;
        this.sessionId = null;
        this.esconderIndicadorXP();
    }
}

// CSS para animações
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
`;
document.head.appendChild(style);

// Disponibilizar globalmente
window.ActivityTracker = ActivityTracker;
