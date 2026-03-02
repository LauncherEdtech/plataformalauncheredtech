// ==================== HELPZONE OVERLAYS JS ====================
// Controla todos os modais e painéis do HelpZone

let currentMediaFile = null;
let currentMediaType = null;
let searchTimeout = null;
let currentSearchTab = 'pessoas';

// ==================== CRIAR POST ====================
function openCreatePostModal() {
    const overlay = document.getElementById('createPostOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Focus no textarea
    setTimeout(() => {
        document.getElementById('postTexto').focus();
    }, 300);
}

function closeCreatePostModal() {
    const overlay = document.getElementById('createPostOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    
    // Limpar form
    document.getElementById('createPostForm').reset();
    document.getElementById('charCount').textContent = '0';
    removeMedia();
}

// Contador de caracteres
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('postTexto');
    if (textarea) {
        textarea.addEventListener('input', function() {
            const count = this.value.length;
            document.getElementById('charCount').textContent = count;
            
            if (count > 450) {
                document.getElementById('charCount').style.color = '#f59e0b';
            } else if (count > 480) {
                document.getElementById('charCount').style.color = '#ef4444';
            } else {
                document.getElementById('charCount').style.color = '#737373';
            }
        });
    }
});

// Handle de seleção de imagem
function handleImageSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validar tipo
    if (!file.type.startsWith('image/')) {
        showToast('Apenas imagens são permitidas', 'error');
        return;
    }
    
    // Validar tamanho (5MB)
    if (file.size > 5 * 1024 * 1024) {
        showToast('Imagem muito grande. Máximo: 5MB', 'error');
        return;
    }
    
    currentMediaFile = file;
    currentMediaType = 'image';
    
    // Preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('mediaPreview');
        const img = document.getElementById('imagePreview');
        const video = document.getElementById('videoPreview');
        
        video.style.display = 'none';
        img.src = e.target.result;
        img.style.display = 'block';
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// Handle de seleção de vídeo
function handleVideoSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validar tipo
    if (!file.type.startsWith('video/')) {
        showToast('Apenas vídeos são permitidos', 'error');
        return;
    }
    
    // Validar tamanho (20MB)
    if (file.size > 20 * 1024 * 1024) {
        showToast('Vídeo muito grande. Máximo: 20MB', 'error');
        return;
    }
    
    currentMediaFile = file;
    currentMediaType = 'video';
    
    // Preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('mediaPreview');
        const img = document.getElementById('imagePreview');
        const video = document.getElementById('videoPreview');
        
        img.style.display = 'none';
        video.src = e.target.result;
        video.style.display = 'block';
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// Remover mídia
function removeMedia() {
    currentMediaFile = null;
    currentMediaType = null;
    
    document.getElementById('mediaPreview').style.display = 'none';
    document.getElementById('imagePreview').src = '';
    document.getElementById('videoPreview').src = '';
    document.getElementById('imageInput').value = '';
    document.getElementById('videoInput').value = '';
}

// Submit do post
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createPostForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const texto = document.getElementById('postTexto').value.trim();
            
            // Validação
            if (!texto && !currentMediaFile) {
                showToast('Adicione texto ou mídia ao post', 'error');
                return;
            }
            
            const btn = document.getElementById('submitPostBtn');
            const btnText = btn.querySelector('.btn-text');
            const btnLoading = btn.querySelector('.btn-loading');
            
            // Loading state
            btn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline-block';
            
            try {
                const formData = new FormData();
                formData.append('texto', texto);
                
                if (currentMediaFile) {
                    formData.append('arquivo', currentMediaFile);
                    formData.append('tipo_midia', currentMediaType);
                } else {
                    formData.append('tipo_midia', 'texto');
                }
                
                const response = await fetch('/helpzone/criar-post', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    showToast('Post criado com sucesso!', 'success');
                    closeCreatePostModal();
                    
                    // Recarregar página após 1s
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    const data = await response.json();
                    showToast(data.error || 'Erro ao criar post', 'error');
                }
            } catch (error) {
                console.error('Erro:', error);
                showToast('Erro ao criar post', 'error');
            } finally {
                btn.disabled = false;
                btnText.style.display = 'inline-block';
                btnLoading.style.display = 'none';
            }
        });
    }
});

// ==================== BUSCA / EXPLORAR ====================
function openSearchModal() {
    const overlay = document.getElementById('searchOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Focus no input
    setTimeout(() => {
        document.getElementById('searchInput').focus();
    }, 300);
    
    // Carregar sugestões iniciais
    loadSearchSuggestions();
}

function closeSearchModal() {
    const overlay = document.getElementById('searchOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    
    // Limpar busca
    document.getElementById('searchInput').value = '';
    clearSearch();
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.querySelector('.search-clear').style.display = 'none';
    loadSearchSuggestions();
}

function switchSearchTab(tab) {
    currentSearchTab = tab;
    
    // Atualizar tabs visuais
    document.querySelectorAll('.search-tab').forEach(t => {
        t.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    // Recarregar resultados
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        performSearch(query, tab);
    } else {
        loadSearchSuggestions();
    }
}

// Input de busca com debounce
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('searchInput');
    if (input) {
        input.addEventListener('input', function() {
            const query = this.value.trim();
            const clearBtn = document.querySelector('.search-clear');
            
            if (query) {
                clearBtn.style.display = 'block';
                
                // Debounce
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    performSearch(query, currentSearchTab);
                }, 500);
            } else {
                clearBtn.style.display = 'none';
                loadSearchSuggestions();
            }
        });
        
        // Enter para buscar
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    performSearch(query, currentSearchTab);
                }
            }
        });
    }
});

// Carregar sugestões (quando não há busca)
async function loadSearchSuggestions() {
    const resultsDiv = document.getElementById('searchResults');
    
    try {
        const response = await fetch('/helpzone/api/sugestoes');
        const data = await response.json();
        
        if (data.success && data.usuarios && data.usuarios.length > 0) {
            resultsDiv.innerHTML = `
                <div style="margin-bottom: 16px;">
                    <h4 style="font-size: 0.9rem; color: #737373; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Sugestões para você
                    </h4>
                </div>
                ${data.usuarios.map(user => `
                    <div class="search-result-item" onclick="location.href='/helpzone/perfil/${user.id}'">
                        <div class="result-avatar">
                            ${user.foto ? `<img src="${user.foto}" alt="${user.nome}">` : user.nome[0].toUpperCase()}
                        </div>
                        <div class="result-info">
                            <div class="result-name">${user.nome}</div>
                            <div class="result-meta">${user.ocupacao || 'Estudante'} • ${user.seguidores} seguidores</div>
                        </div>
                        <button class="result-action" onclick="event.stopPropagation(); followUser(${user.id}, this)">
                            Seguir
                        </button>
                    </div>
                `).join('')}
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="search-empty">
                    <i class="fas fa-users" style="font-size: 3rem; opacity: 0.3;"></i>
                    <p>Nenhuma sugestão disponível</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar sugestões:', error);
        resultsDiv.innerHTML = `
            <div class="search-empty">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; opacity: 0.3;"></i>
                <p>Erro ao carregar sugestões</p>
            </div>
        `;
    }
}

// Realizar busca
async function performSearch(query, tipo) {
    const resultsDiv = document.getElementById('searchResults');
    const loadingDiv = document.getElementById('searchLoading');
    
    resultsDiv.style.display = 'none';
    loadingDiv.style.display = 'block';
    
    try {
        const response = await fetch(`/helpzone/buscar?q=${encodeURIComponent(query)}&tipo=${tipo}`);
        const html = await response.text();
        
        // Parse HTML para extrair resultados
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        loadingDiv.style.display = 'none';
        resultsDiv.style.display = 'block';
        
        if (tipo === 'pessoas') {
            renderPessoasResults(doc, query);
        } else if (tipo === 'posts') {
            renderPostsResults(doc, query);
        } else if (tipo === 'hashtags') {
            renderHashtagsResults(doc, query);
        }
    } catch (error) {
        console.error('Erro na busca:', error);
        loadingDiv.style.display = 'none';
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = `
            <div class="search-empty">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; opacity: 0.3;"></i>
                <p>Erro ao buscar</p>
            </div>
        `;
    }
}

function renderPessoasResults(doc, query) {
    const resultsDiv = document.getElementById('searchResults');
    
    // Simular resultados (você precisará ajustar conforme sua API)
    resultsDiv.innerHTML = `
        <div style="margin-bottom: 16px;">
            <h4 style="font-size: 0.9rem; color: #737373; margin-bottom: 12px;">
                Resultados para "${query}"
            </h4>
        </div>
        <div class="search-empty">
            <i class="fas fa-search" style="font-size: 3rem; opacity: 0.3;"></i>
            <p>Use a página de busca completa para resultados detalhados</p>
            <button class="btn-primary" onclick="window.location.href='/helpzone/buscar?q=${encodeURIComponent(query)}&tipo=pessoas'" style="margin-top: 16px;">
                Ver todos os resultados
            </button>
        </div>
    `;
}

function renderPostsResults(doc, query) {
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = `
        <div class="search-empty">
            <i class="fas fa-images" style="font-size: 3rem; opacity: 0.3;"></i>
            <p>Use a página de busca completa para ver posts</p>
            <button class="btn-primary" onclick="window.location.href='/helpzone/buscar?q=${encodeURIComponent(query)}&tipo=posts'" style="margin-top: 16px;">
                Ver todos os posts
            </button>
        </div>
    `;
}

function renderHashtagsResults(doc, query) {
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = `
        <div class="search-empty">
            <i class="fas fa-hashtag" style="font-size: 3rem; opacity: 0.3;"></i>
            <p>Use a página de busca completa para ver hashtags</p>
            <button class="btn-primary" onclick="window.location.href='/helpzone/buscar?q=${encodeURIComponent(query)}&tipo=hashtags'" style="margin-top: 16px;">
                Ver todas as hashtags
            </button>
        </div>
    `;
}

// ==================== NOTIFICAÇÕES ====================
function openNotificationsPanel() {
    const overlay = document.getElementById('notificationsOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Carregar notificações
    loadNotifications();
}

function closeNotificationsPanel() {
    const overlay = document.getElementById('notificationsOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
}

async function loadNotifications() {
    const listDiv = document.getElementById('notificationsList');
    
    try {
        const response = await fetch('/helpzone/api/notificacoes');
        const data = await response.json();
        
        if (data.success && data.notificacoes && data.notificacoes.length > 0) {
            listDiv.innerHTML = data.notificacoes.map(notif => `
                <div class="notification-item ${notif.lida ? '' : 'unread'}" onclick="handleNotificationClick(${notif.id}, '${notif.link}')">
                    <div class="notif-avatar">
                        ${notif.foto ? `<img src="${notif.foto}" alt="${notif.origem}">` : notif.origem[0].toUpperCase()}
                    </div>
                    <div class="notif-content">
                        <div class="notif-text">${notif.mensagem}</div>
                        <div class="notif-time">${notif.tempo}</div>
                    </div>
                </div>
            `).join('');
        } else {
            listDiv.innerHTML = `
                <div class="notifications-empty">
                    <i class="far fa-bell"></i>
                    <h4 style="margin-top: 12px; color: #ffffff;">Nenhuma notificação</h4>
                    <p>Você está em dia!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar notificações:', error);
        listDiv.innerHTML = `
            <div class="notifications-empty">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Erro ao carregar notificações</p>
            </div>
        `;
    }
}

function handleNotificationClick(notifId, link) {
    // Marcar como lida
    fetch(`/helpzone/api/notificacao/${notifId}/ler`, {
        method: 'POST'
    });
    
    // Redirecionar
    if (link) {
        window.location.href = link;
    }
}

// ==================== UTILITÁRIOS ====================
function showToast(message, type = 'info') {
    // Remover toasts existentes
    document.querySelectorAll('.toast').forEach(t => t.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function followUser(userId, button) {
    try {
        const response = await fetch(`/helpzone/api/user/${userId}/follow`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.seguindo) {
                button.textContent = 'Seguindo';
                button.classList.add('following');
                showToast('Agora você está seguindo', 'success');
            } else {
                button.textContent = 'Seguir';
                button.classList.remove('following');
                showToast('Deixou de seguir', 'info');
            }
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao seguir', 'error');
    }
}

// ==================== FECHAR MODAIS COM ESC ====================
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (document.getElementById('createPostOverlay').classList.contains('active')) {
            closeCreatePostModal();
        }
        if (document.getElementById('searchOverlay').classList.contains('active')) {
            closeSearchModal();
        }
        if (document.getElementById('notificationsOverlay').classList.contains('active')) {
            closeNotificationsPanel();
        }
    }
});

console.log('✅ HelpZone Overlays JS carregado!');
