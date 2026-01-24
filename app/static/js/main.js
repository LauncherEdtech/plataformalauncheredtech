// static/js/main.js - Arquivo JavaScript principal da Plataforma Launcher

// Funções utilitárias globais
function showToast(message, type = 'info', duration = 5000) {
    /**
     * Exibe uma notificação toast
     * @param {string} message - Mensagem a ser exibida
     * @param {string} type - Tipo: success, error, warning, info
     * @param {number} duration - Duração em ms
     */
    
    // Remover toast existente se houver
    const existingToast = document.getElementById('global-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Criar novo toast
    const toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
    toast.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 300px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        border-radius: 10px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>${message}</span>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Animar entrada
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remover
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// Função para formatar tempo em string legível
function formatarTempo(minutos) {
    if (minutos === 0) return "0h";
    
    const horas = Math.floor(minutos / 60);
    const min = minutos % 60;
    
    if (horas > 0) {
        if (min > 0) {
            return `${horas}h${min.toString().padStart(2, '0')}`;
        } else {
            return `${horas}h`;
        }
    } else {
        return `${min}min`;
    }
}

// Função para animar contadores
function animateCounter(element, targetValue, duration = 1000) {
    const startValue = 0;
    const increment = targetValue / (duration / 16);
    let currentValue = startValue;
    
    const timer = setInterval(() => {
        currentValue += increment;
        if (currentValue >= targetValue) {
            element.textContent = targetValue;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(currentValue);
        }
    }, 16);
}

// Sistema de confirmação de ações
function confirmarAcao(mensagem, callback) {
    const confirmModal = document.createElement('div');
    confirmModal.className = 'modal fade';
    confirmModal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-white">
                <div class="modal-header">
                    <h5 class="modal-title">Confirmação</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${mensagem}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="button" class="btn btn-primary" id="confirm-action">Confirmar</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(confirmModal);
    
    const modal = new bootstrap.Modal(confirmModal);
    modal.show();
    
    document.getElementById('confirm-action').addEventListener('click', () => {
        callback();
        modal.hide();
        confirmModal.remove();
    });
    
    confirmModal.addEventListener('hidden.bs.modal', () => {
        confirmModal.remove();
    });
}

// Função para validar formulários
function validarFormulario(formId, regras) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let valido = true;
    
    for (const campo in regras) {
        const input = form.querySelector(`[name="${campo}"]`);
        if (!input) continue;
        
        const valor = input.value.trim();
        const regra = regras[campo];
        
        // Remover classes de erro anteriores
        input.classList.remove('is-invalid');
        const feedback = input.parentElement.querySelector('.invalid-feedback');
        if (feedback) feedback.remove();
        
        // Validar campo obrigatório
        if (regra.obrigatorio && !valor) {
            mostrarErroValidacao(input, regra.mensagem || 'Este campo é obrigatório');
            valido = false;
            continue;
        }
        
        // Validar tamanho mínimo
        if (regra.minimo && valor.length < regra.minimo) {
            mostrarErroValidacao(input, `Deve ter pelo menos ${regra.minimo} caracteres`);
            valido = false;
            continue;
        }
        
        // Validar email
        if (regra.email && valor && !isEmailValido(valor)) {
            mostrarErroValidacao(input, 'Email inválido');
            valido = false;
            continue;
        }
        
        // Validar números
        if (regra.numero && valor && isNaN(valor)) {
            mostrarErroValidacao(input, 'Deve ser um número válido');
            valido = false;
            continue;
        }
    }
    
    return valido;
}

function mostrarErroValidacao(input, mensagem) {
    input.classList.add('is-invalid');
    
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    feedback.textContent = mensagem;
    
    input.parentElement.appendChild(feedback);
}

function isEmailValido(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Sistema de loading global
function showLoading(texto = 'Carregando...') {
    const loading = document.createElement('div');
    loading.id = 'global-loading';
    loading.className = 'position-fixed w-100 h-100 d-flex align-items-center justify-content-center';
    loading.style.cssText = `
        top: 0; left: 0; z-index: 9999;
        background-color: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(5px);
    `;
    
    loading.innerHTML = `
        <div class="text-center text-white">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>${texto}</div>
        </div>
    `;
    
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('global-loading');
    if (loading) {
        loading.remove();
    }
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss de alerts após 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-dismissible')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
    
    // Smooth scroll para links âncora
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Animação de fade-in para elementos com classe fade-in
    const fadeElements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    fadeElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Função para debounce (evitar muitas chamadas de função)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Sistema de busca em tempo real
function setupLiveSearch(inputId, resultContainerId, searchFunction) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(resultContainerId);
    
    if (!input || !container) return;
    
    const debouncedSearch = debounce(searchFunction, 300);
    
    input.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            debouncedSearch(query, container);
        } else {
            container.innerHTML = '';
        }
    });
}

// Utilitário para fazer requisições AJAX
async function fetchAPI(url, options = {}) {
    try {
        showLoading();
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('API Error:', error);
        showToast('Erro na comunicação com o servidor', 'error');
        throw error;
    } finally {
        hideLoading();
    }
}

// Exportar funções para uso global
window.LauncherUtils = {
    showToast,
    formatarTempo,
    animateCounter,
    confirmarAcao,
    validarFormulario,
    showLoading,
    hideLoading,
    debounce,
    setupLiveSearch,
    fetchAPI
};

console.log('🚀 Plataforma Launcher - JavaScript carregado com sucesso!');