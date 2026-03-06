/**
 * HELPZONE OVERLAYS - VERSÃO MELHORADA
 * Com tratamento de erros robusto e fallbacks
 */

(function() {
    'use strict';

    // ================================================
    // ESTADO GLOBAL
    // ================================================
    const HelpZoneOverlays = {
        activeOverlay: null,
        createPostData: {
            text: '',
            mediaFile: null,
            mediaType: null
        },
        searchHistory: []
    };

    // ================================================
    // MODAL DE CRIAR POST
    // ================================================
    window.openCreatePostModal = function() {
        const overlay = document.getElementById('hzCreatePostOverlay');
        if (!overlay) {
            console.error('❌ Overlay de criar post não encontrado');
            return;
        }

        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        HelpZoneOverlays.activeOverlay = 'create';

        // Focus no textarea
        setTimeout(() => {
            const textarea = document.getElementById('hzPostText');
            if (textarea) textarea.focus();
        }, 300);
        
        console.log('✅ Modal de criar post aberto');
    };

    window.closeCreatePostModal = function() {
        const overlay = document.getElementById('hzCreatePostOverlay');
        if (!overlay) return;

        const textarea = document.getElementById('hzPostText');
        const hasContent = textarea && textarea.value.trim();
        const hasMedia = HelpZoneOverlays.createPostData.mediaFile;

        // Confirmar se houver conteúdo
        if (hasContent || hasMedia) {
            if (!confirm('Descartar publicação?')) {
                return;
            }
        }

        overlay.classList.remove('active');
        document.body.style.overflow = '';
        HelpZoneOverlays.activeOverlay = null;

        // Limpar dados
        setTimeout(() => {
            if (textarea) textarea.value = '';
            clearCreatePostMedia();
            updatePublishButton();
        }, 300);
        
        console.log('✅ Modal de criar post fechado');
    };

    // ================================================
    // CRIAR POST - VALIDAÇÃO
    // ================================================
    window.updatePublishButton = function() {
        const textarea = document.getElementById('hzPostText');
        const publishBtn = document.getElementById('hzPublishBtn');
        
        if (!textarea || !publishBtn) return;

        const hasText = textarea.value.trim().length > 0;
        const hasMedia = HelpZoneOverlays.createPostData.mediaFile !== null;

        publishBtn.disabled = !hasText && !hasMedia;
    };

    // ================================================
    // CRIAR POST - UPLOAD DE MÍDIA
    // ================================================
    window.triggerMediaUpload = function(type) {
        const fileInput = document.getElementById('hzMediaInput');
        if (!fileInput) {
            console.error('❌ Input de arquivo não encontrado');
            return;
        }

        fileInput.value = '';
        
        if (type === 'image') {
            fileInput.accept = 'image/png,image/jpeg,image/jpg,image/gif,image/webp';
            HelpZoneOverlays.createPostData.mediaType = 'image';
        } else if (type === 'video') {
            fileInput.accept = 'video/mp4,video/webm,video/mov';
            HelpZoneOverlays.createPostData.mediaType = 'video';
        }

        fileInput.click();
    };

    window.handleMediaUpload = function(input) {
        const file = input.files[0];
        if (!file) return;

        const maxSize = HelpZoneOverlays.createPostData.mediaType === 'image' 
            ? 5 * 1024 * 1024  // 5MB
            : 50 * 1024 * 1024; // 50MB

        if (file.size > maxSize) {
            showToast(`Arquivo muito grande! Limite: ${maxSize / (1024 * 1024)}MB`, 'error');
            clearCreatePostMedia();
            return;
        }

        const reader = new FileReader();

        reader.onload = function(e) {
            const preview = document.getElementById('hzMediaPreview');
            const imgPreview = document.getElementById('hzMediaPreviewImg');
            const vidPreview = document.getElementById('hzMediaPreviewVid');

            if (!preview || !imgPreview || !vidPreview) {
                console.error('❌ Elementos de preview não encontrados');
                return;
            }

            preview.classList.add('show');

            if (HelpZoneOverlays.createPostData.mediaType === 'image') {
                imgPreview.src = e.target.result;
                imgPreview.style.display = 'block';
                vidPreview.style.display = 'none';
                vidPreview.src = '';
            } else if (HelpZoneOverlays.createPostData.mediaType === 'video') {
                vidPreview.src = e.target.result;
                vidPreview.style.display = 'block';
                imgPreview.style.display = 'none';
                imgPreview.src = '';

                // Validar duração
                vidPreview.onloadedmetadata = function() {
                    if (this.duration > 60) { // Aumentei para 60s
                        showToast('Vídeo muito longo! Limite: 60 segundos.', 'error');
                        clearCreatePostMedia();
                    }
                };
            }

            HelpZoneOverlays.createPostData.mediaFile = file;
            updatePublishButton();
            console.log('✅ Mídia carregada:', file.name);
        };

        reader.readAsDataURL(file);
    };

    window.clearCreatePostMedia = function() {
        const fileInput = document.getElementById('hzMediaInput');
        const preview = document.getElementById('hzMediaPreview');
        const imgPreview = document.getElementById('hzMediaPreviewImg');
        const vidPreview = document.getElementById('hzMediaPreviewVid');

        if (fileInput) fileInput.value = '';
        if (preview) preview.classList.remove('show');
        if (imgPreview) {
            imgPreview.src = '';
            imgPreview.style.display = 'none';
        }
        if (vidPreview) {
            vidPreview.src = '';
            vidPreview.style.display = 'none';
        }

        HelpZoneOverlays.createPostData.mediaFile = null;
        HelpZoneOverlays.createPostData.mediaType = null;
        updatePublishButton();
        console.log('✅ Mídia removida');
    };

    // ================================================
    // CRIAR POST - SUBMIT
    // ================================================
    window.submitCreatePost = async function() {
        const textarea = document.getElementById('hzPostText');
        const publishBtn = document.getElementById('hzPublishBtn');

        if (!textarea || !publishBtn) return;

        const text = textarea.value.trim();
        const file = HelpZoneOverlays.createPostData.mediaFile;

        if (!text && !file) {
            showToast('Escreva algo ou adicione uma foto/vídeo!', 'error');
            return;
        }

        // Loading state
        publishBtn.disabled = true;
        publishBtn.classList.add('loading');
        publishBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const formData = new FormData();
            formData.append('texto', text);
            
            if (file) {
                formData.append('arquivo', file);
                formData.append('tipo_midia', HelpZoneOverlays.createPostData.mediaType);
            } else {
                formData.append('tipo_midia', 'texto');
            }

            const response = await fetch('/helpzone/criar-post', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                showToast('Post criado com sucesso!', 'success');
                
                // Fechar modal
                closeCreatePostModal();
                
                // Recarregar feed após 500ms
                setTimeout(() => {
                    window.location.href = '/helpzone/feed';
                }, 500);
            } else {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.message || 'Erro ao criar post');
            }
        } catch (error) {
            console.error('❌ Erro ao criar post:', error);
            showToast(error.message || 'Erro ao publicar. Tente novamente.', 'error');
            
            publishBtn.disabled = false;
            publishBtn.classList.remove('loading');
            publishBtn.innerHTML = 'Publicar';
        }
    };

    // ================================================
    // PAINEL DE NOTIFICAÇÕES
    // ================================================
    window.openNotificationsPanel = function() {
        const panel = document.getElementById('hzNotificationsPanel');
        const overlay = document.getElementById('hzNotificationsOverlay');
        
        if (!panel || !overlay) {
            console.error('❌ Painel de notificações não encontrado');
            showToast('Painel de notificações não disponível', 'error');
            return;
        }

        overlay.classList.add('active');
        panel.classList.add('active');
        document.body.style.overflow = 'hidden';
        HelpZoneOverlays.activeOverlay = 'notifications';

        // Carregar notificações
        loadNotifications();
        
        console.log('✅ Painel de notificações aberto');
    };

    window.closeNotificationsPanel = function() {
        const panel = document.getElementById('hzNotificationsPanel');
        const overlay = document.getElementById('hzNotificationsOverlay');
        
        if (!panel || !overlay) return;

        overlay.classList.remove('active');
        panel.classList.remove('active');
        document.body.style.overflow = '';
        HelpZoneOverlays.activeOverlay = null;
        
        console.log('✅ Painel de notificações fechado');
    };

    async function loadNotifications() {
        const container = document.getElementById('hzNotificationsList');
        if (!container) return;

        container.innerHTML = '<div class="hz-loading"><div class="hz-spinner"></div></div>';

        try {
            const response = await fetch('/helpzone/api/notificacoes');
            
            if (!response.ok) {
                throw new Error('Erro ao carregar notificações');
            }
            
            const data = await response.json();

            if (data.success && data.notificacoes && data.notificacoes.length > 0) {
                container.innerHTML = data.notificacoes.map(notif => `
                    <div class="hz-notification-item ${notif.lida ? '' : 'unread'}" 
                         onclick="handleNotificationClick(${notif.id}, '${notif.link || '#'}')">
                        <div class="hz-notification-avatar">
                            ${notif.usuario_foto 
                                ? `<img src="${notif.usuario_foto}" alt="${notif.usuario_nome}">`
                                : notif.usuario_nome[0].toUpperCase()
                            }
                        </div>
                        <div class="hz-notification-content">
                            <div class="hz-notification-text">
                                <strong>${notif.usuario_nome}</strong> ${notif.mensagem}
                            </div>
                            <div class="hz-notification-time">${notif.tempo}</div>
                        </div>
                        ${!notif.lida ? '<div class="hz-notification-indicator"></div>' : ''}
                    </div>
                `).join('');
                
                console.log(`✅ ${data.notificacoes.length} notificações carregadas`);
            } else {
                container.innerHTML = `
                    <div class="hz-empty-state">
                        <i class="far fa-bell"></i>
                        <h3>Sem notificações</h3>
                        <p>Quando alguém interagir com você, aparecerá aqui</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('❌ Erro ao carregar notificações:', error);
            container.innerHTML = `
                <div class="hz-empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erro ao carregar</h3>
                    <p>Verifique sua conexão e tente novamente</p>
                </div>
            `;
        }
    }

    window.handleNotificationClick = async function(notifId, link) {
        // Marcar como lida
        try {
            await fetch(`/helpzone/api/notificacao/${notifId}/marcar-lida`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('❌ Erro ao marcar notificação:', error);
        }

        // Navegar
        if (link && link !== '#') {
            window.location.href = link;
        }
    };

    window.switchNotificationTab = function(tab) {
        console.log('🔄 Mudando para tab:', tab);
        // TODO: Implementar filtro de tabs
    };

    // ================================================
    // MODAL DE BUSCA
    // ================================================
    window.openSearchModal = function() {
        const overlay = document.getElementById('hzSearchOverlay');
        if (!overlay) {
            console.error('❌ Modal de busca não encontrado');
            showToast('Busca não disponível', 'error');
            return;
        }

        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        HelpZoneOverlays.activeOverlay = 'search';

        // Focus no input
        setTimeout(() => {
            const input = document.getElementById('hzSearchInput');
            if (input) input.focus();
        }, 300);

        // Carregar buscas recentes
        loadRecentSearches();
        
        console.log('✅ Modal de busca aberto');
    };

    window.closeSearchModal = function() {
        const overlay = document.getElementById('hzSearchOverlay');
        if (!overlay) return;

        overlay.classList.remove('active');
        document.body.style.overflow = '';
        HelpZoneOverlays.activeOverlay = null;
        
        console.log('✅ Modal de busca fechado');
    };

    window.handleSearchInput = function(input) {
        const clearBtn = document.getElementById('hzSearchClearBtn');

        if (input.value.trim()) {
            if (clearBtn) clearBtn.classList.add('show');
            performSearch(input.value);
        } else {
            if (clearBtn) clearBtn.classList.remove('show');
            loadRecentSearches();
        }
    };

    window.clearSearchInput = function() {
        const input = document.getElementById('hzSearchInput');
        const clearBtn = document.getElementById('hzSearchClearBtn');
        
        if (input) {
            input.value = '';
            input.focus();
        }
        if (clearBtn) clearBtn.classList.remove('show');
        
        loadRecentSearches();
    };



    async function loadRecentSearches() {
        const container = document.getElementById('hzSearchResults');
        if (!container) return;

        // Simulação - implementar com API real
        const recent = [
            { type: 'user', name: 'Busque usuários, posts e hashtags', icon: 'search' }
        ];

        container.innerHTML = `
            <div class="hz-empty-state">
                <i class="fas fa-search"></i>
                <h3>Buscar na HelpZone</h3>
                <p>Digite para encontrar pessoas, posts e hashtags</p>
            </div>
        `;
    }

    async function performSearch(query) {
        const container = document.getElementById('hzSearchResults');
        if (!container) return;

        container.innerHTML = '<div class="hz-loading"><div class="hz-spinner"></div></div>';

        try {
            const response = await fetch(`/helpzone/api/buscar?q=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error('Erro na busca');
            }
            
            const data = await response.json();

            // Renderizar resultados
            if (data.success && (data.usuarios?.length > 0 || data.posts?.length > 0 || data.hashtags?.length > 0)) {
                let html = '';
                
                if (data.usuarios && data.usuarios.length > 0) {
                    html += data.usuarios.map(user => `
                        <div class="hz-recent-item" onclick="window.location.href='/helpzone/perfil/${user.id}'">
                            <div class="hz-notification-avatar">
                                ${user.foto ? `<img src="${user.foto}" alt="${user.nome}">` : user.nome[0].toUpperCase()}
                            </div>
                            <div class="hz-recent-info">
                                <div class="hz-recent-name">${user.nome}</div>
                                <div class="hz-recent-type">Usuário</div>
                            </div>
                        </div>
                    `).join('');
                }
                
                container.innerHTML = `<div class="hz-search-results-list">${html}</div>`;
                console.log(`✅ Busca realizada: ${query}`);
            } else {
                container.innerHTML = `
                    <div class="hz-empty-state">
                        <i class="fas fa-search"></i>
                        <h3>Nenhum resultado</h3>
                        <p>Tente buscar com outros termos</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('❌ Erro na busca:', error);
            container.innerHTML = `
                <div class="hz-empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erro na busca</h3>
                    <p>Verifique sua conexão e tente novamente</p>
                </div>
            `;
        }
    }

    window.selectRecentSearch = function(query) {
        const input = document.getElementById('hzSearchInput');
        if (input) {
            input.value = query;
            performSearch(query);
        }
    };

    window.clearRecentSearches = function() {
        HelpZoneOverlays.searchHistory = [];
        loadRecentSearches();
    };

    window.removeRecentSearch = function(query) {
        HelpZoneOverlays.searchHistory = HelpZoneOverlays.searchHistory.filter(item => item !== query);
        loadRecentSearches();
    };

    window.switchSearchTab = function(tab) {
        const tabs = document.querySelectorAll('.hz-search-tab');
        tabs.forEach(t => t.classList.remove('active'));
        event.target.classList.add('active');
        
        console.log('🔄 Mudando para tab de busca:', tab);
    };

    // ================================================
    // TOAST NOTIFICATIONS
    // ================================================
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        toast.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            padding: 14px 24px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#8b5cf6'};
            color: white;
            border-radius: 12px;
            font-size: 0.95rem;
            font-weight: 600;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.style.opacity = '1', 10);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Tornar showToast global
    window.showToast = showToast;

    // ================================================
    // ATALHOS DE TECLADO
    // ================================================
    document.addEventListener('keydown', function(e) {
        // ESC para fechar overlay ativo
        if (e.key === 'Escape' && HelpZoneOverlays.activeOverlay) {
            switch (HelpZoneOverlays.activeOverlay) {
                case 'create':
                    closeCreatePostModal();
                    break;
                case 'notifications':
                    closeNotificationsPanel();
                    break;
                case 'search':
                    closeSearchModal();
                    break;
            }
        }

        // Ctrl/Cmd + K para busca
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        }

        // Ctrl/Cmd + Enter para publicar (se modal de criar estiver aberto)
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && HelpZoneOverlays.activeOverlay === 'create') {
            const publishBtn = document.getElementById('hzPublishBtn');
            if (publishBtn && !publishBtn.disabled) {
                submitCreatePost();
            }
        }
    });

    // ================================================
    // INICIALIZAÇÃO
    // ================================================
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ HelpZone Overlays (v2) inicializado');

        // Auto-resize textarea
        const textarea = document.getElementById('hzPostText');
        if (textarea) {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 300) + 'px';
                updatePublishButton();
            });
        }

        // Listener para input de mídia
        const mediaInput = document.getElementById('hzMediaInput');
        if (mediaInput) {
            mediaInput.addEventListener('change', function() {
                handleMediaUpload(this);
            });
        }

        // Listener para busca
        const searchInput = document.getElementById('hzSearchInput');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    handleSearchInput(this);
                }, 300);
            });
        }

        // Verificar se todos os elementos necessários existem
        const requiredElements = [
            'hzCreatePostOverlay',
            'hzNotificationsPanel',
            'hzNotificationsOverlay',
            'hzSearchOverlay'
        ];

        requiredElements.forEach(id => {
            const element = document.getElementById(id);
            if (!element) {
                console.warn(`⚠️ Elemento ${id} não encontrado`);
            }
        });
    });

    // Prevenir scroll do body quando overlay estiver aberto
    window.addEventListener('touchmove', function(e) {
        if (HelpZoneOverlays.activeOverlay && e.target.closest('.hz-modal-body, .hz-panel-body, .hz-search-results')) {
            return;
        }
        if (HelpZoneOverlays.activeOverlay) {
            e.preventDefault();
        }
    }, { passive: false });

})();
