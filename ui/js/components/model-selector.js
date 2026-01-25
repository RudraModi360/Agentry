/**
 * AGENTRY UI - Model Selector Component
 * Handles the ChatGPT-style Agentry dropdown for provider/model selection.
 */

const ModelSelector = (function () {
    'use strict';

    // Provider Data - Same 4 providers as setup page
    const PROVIDERS = [
        {
            id: 'ollama',
            name: 'Ollama',
            icon: 'https://github.com/ollama.png',
            description: 'Local + Cloud',
            models: []
        },
        {
            id: 'groq',
            name: 'Groq',
            icon: 'https://github.com/groq.png',
            description: 'Cloud API',
            models: []
        },
        {
            id: 'gemini',
            name: 'Gemini',
            icon: 'https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg',
            description: 'Cloud API',
            models: []
        },
        {
            id: 'azure',
            name: 'Azure OpenAI',
            icon: 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Microsoft_Azure.svg',
            description: 'Cloud API',
            models: []
        },
        {
            id: 'llama_cpp',
            name: 'Llama Cpp',
            icon: 'https://github.com/ggerganov/llama.cpp/raw/master/media/llama.cpp.png',
            description: 'Local GGUF',
            models: []
        }
    ];

    // State - populated from API/localStorage
    const state = {
        isOpen: false,
        currentModel: null,
        currentProvider: null,
        currentModelType: null,
        savedConfigs: [] // Cache for configured models
    };

    // DOM Elements cache
    const elements = {};

    /**
     * Initialize the component
     */
    async function init() {
        console.log('[ModelSelector] Initializing...');
        cacheElements();
        console.log('[ModelSelector] Elements cached:', elements);

        // Wait for current model sync
        await syncCurrentModel();

        // Fetch saved configs
        await fetchSavedConfigs();

        setupEventListeners();
        console.log('[ModelSelector] Initialization complete');
    }

    /**
     * Cache DOM elements
     */
    function cacheElements() {
        elements.agentryDropdown = document.getElementById('agentry-dropdown');
        elements.agentryBtn = document.getElementById('agentry-dropdown-btn');
        elements.providerPopup = document.getElementById('provider-popup');
        elements.providerPopupList = document.getElementById('provider-popup-list');
        elements.gotoSettings = document.getElementById('provider-goto-settings');
        elements.headerModelLabel = document.getElementById('header-model-label');

        // Provider Config Modal
        elements.configModalOverlay = document.getElementById('provider-config-modal-overlay');
        elements.configEditor = document.getElementById('provider-config-editor');
        elements.configError = document.getElementById('provider-config-error');
        elements.configSaveBtn = document.getElementById('provider-config-save-btn');
        elements.configCloseBtn = document.getElementById('provider-config-close-btn');

        // Saved Models Modal
        elements.savedModelsModalOverlay = document.getElementById('saved-models-modal-overlay');
        elements.savedModelsList = document.getElementById('saved-models-list');
        elements.savedModelsCloseBtn = document.getElementById('saved-models-close-btn');
    }

    /**
     * Render provider items in the popup
     */
    /**
     * Render a single provider item HTML
     */
    /**
     * Render a single provider item HTML
     */
    function renderItemHtml(item, isModal = false) {
        const active = isCurrent(item.provider, item.model);
        return `
            <div class="provider-popup-item ${active ? 'active' : ''}" 
                 data-provider-id="${item.provider}" 
                 data-model-id="${item.model}">
                <div class="provider-popup-item-icon">
                    <img src="${item.icon}" alt="${item.providerName}" style="width: 100%; height: 100%; object-fit: contain;" onerror="this.style.display='none'">
                </div>
                <div class="provider-popup-item-info">
                    <div class="provider-popup-item-name">${item.model}</div>
                    <div class="provider-popup-item-model">${item.providerName}</div>
                </div>
                <div class="provider-popup-item-actions" style="display: flex; align-items: center; gap: 8px;">
                    ${active ? `
                    <svg class="provider-popup-item-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="width: 16px; height: 16px; color: var(--accent-color);">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>` : ''}
                    <button class="provider-edit-btn" style="background: none; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 4px; display: flex;" title="Edit Configuration">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    ${item.isSaved ? `
                    <button class="provider-delete-btn" style="background: none; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 4px; display: flex;" title="Delete Configuration">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                    </button>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Render provider items in the popup based on history
     */
    function renderProviderPopup() {
        if (!elements.providerPopupList) return;

        let html = '';
        const seen = new Set();

        // Helper to get item data
        const createItem = (p, m, isSaved = false) => {
            const info = getProviderInfo(p);
            return {
                provider: p,
                model: m,
                providerName: info ? info.name : p,
                icon: info ? info.icon : '',
                isSaved: isSaved
            };
        };

        // 1. Current Active Model
        if (state.currentProvider && state.currentModel) {
            const key = `${state.currentProvider}:${state.currentModel}`;
            seen.add(key);
            const item = createItem(state.currentProvider, state.currentModel, false);
            const isSaved = state.savedConfigs.some(c => c.provider === state.currentProvider && c.model === state.currentModel);
            item.isSaved = isSaved;
            html += renderItemHtml(item);
        }

        // 2. Recent/Saved Models (Top 3 Only)
        // Combine session history and saved configs, deduplicate, and take top 3
        const candidates = [];

        // Add saved configs first
        const saved = (state.savedConfigs || []).filter(c => c.model);
        saved.forEach(c => {
            if (!seen.has(`${c.provider}:${c.model}`)) {
                // candidates.push(createItem(c.provider, c.model, true));
                // Don't modify candidates yet, we want to respect session order if possible?
                // Actually user said "recent model show top 3 from that list itself".
                // Let's prioritize recent sessions, but ensure we mark them as saved if they are.
            }
        });

        // Let's build a unified list from recent sessions first, then append other saved keys
        if (window.Sessions && window.Sessions.allSessions) {
            for (const s of window.Sessions.allSessions) {
                if (!s.provider || !s.model) continue;
                const key = `${s.provider}:${s.model}`;

                // Check if this model is in our saved list to mark it
                const isSaved = saved.some(c => c.provider === s.provider && c.model === s.model);

                if (!seen.has(key)) {
                    candidates.push(createItem(s.provider, s.model, isSaved));
                    seen.add(key);
                }
            }
        }

        // Now add any remaining saved configs that weren't in sessions (if we need to fill up to 3)
        saved.forEach(c => {
            const key = `${c.provider}:${c.model}`;
            if (!seen.has(key)) {
                candidates.push(createItem(c.provider, c.model, true));
                seen.add(key);
            }
        });

        // Take only top 3
        const recentToShow = candidates.slice(0, 3);

        if (recentToShow.length > 0) {
            html += `<div class="provider-popup-header" style="margin-top: 8px; border-top: 1px solid var(--border-color); padding-top: 12px;">Recent</div>`;
            recentToShow.forEach(item => {
                html += renderItemHtml(item);
            });
        }

        // 3. "View All Saved Models" Button
        if (saved.length > 0) {
            html += `<div style="height: 1px; background: var(--border-color); margin: 4px 0;"></div>`;
            html += `
                <div class="provider-popup-item manage-item" id="provider-view-saved-btn">
                    <div class="provider-popup-item-icon">
                         <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </div>
                    <div class="provider-popup-item-info">
                        <div class="provider-popup-item-name">View All Saved Models</div>
                    </div>
                     <div style="font-size: 11px; color: var(--text-muted); background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 10px;">${saved.length}</div>
                </div>
            `;
        }

        if (!html) {
            html += `<div class="provider-popup-empty" style="padding: 12px; font-size: 13px; color: var(--text-secondary); text-align: center;">No models found</div>`;
        }

        // Add Manage Button Divider
        html += `<div style="height: 1px; background: var(--border-color); margin: 4px 0;"></div>`;

        // Add Manage Button with Settings Icon
        html += `
            <div class="provider-popup-item manage-item" id="provider-manage-btn">
                <div class="provider-popup-item-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z"></path>
                    </svg>
                </div>
                <div class="provider-popup-item-info">
                    <div class="provider-popup-item-name">Add New Model</div>
                </div>
            </div>
        `;

        elements.providerPopupList.innerHTML = html;

        // Attach click handlers
        elements.providerPopupList.querySelectorAll('.provider-popup-item:not(.manage-item)').forEach(item => {
            // Main item click Selects model
            item.addEventListener('click', (e) => {
                // Ignore if clicked on the edit button
                if (e.target.closest('.provider-edit-btn') || e.target.closest('.provider-delete-btn')) return;

                e.stopPropagation();
                const providerId = item.dataset.providerId;
                const modelId = item.dataset.modelId;
                selectModelFromHistory(providerId, modelId);
            });

            // Edit button handler
            const editBtn = item.querySelector('.provider-edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', (e) => {
                    e.stopPropagation(); // prevent selection
                    const providerId = item.dataset.providerId;
                    const modelId = item.dataset.modelId;
                    openProviderConfig(providerId, modelId);
                });
            }

            // Delete button handler
            const deleteBtn = item.querySelector('.provider-delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation(); // prevent selection
                    const providerId = item.dataset.providerId;
                    const modelId = item.dataset.modelId;
                    deleteProviderConfig(providerId, modelId);
                });
            }
        });

        // View All Saved Models Handler
        const viewSavedBtn = document.getElementById('provider-view-saved-btn');
        if (viewSavedBtn) {
            viewSavedBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeDropdown();
                openSavedModelsModal();
            });
        }

        // Attach Manage Handler
        const manageBtn = document.getElementById('provider-manage-btn');
        if (manageBtn) {
            manageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeDropdown();
                window.location.href = '/setup.html';
            });
        }
    }

    /**
     * Check if item is current active model
     */
    function isCurrent(provider, model) {
        return state.currentProvider === provider && state.currentModel === model;
    }

    /**
     * Get recent models from session history
     */
    function getRecentModelsFromHistory() {
        console.log('[ModelSelector] getRecentModelsFromHistory called');

        const unique = [];
        const seen = new Set();

        // 1. ALWAYS add current model first if it exists
        if (state.currentProvider && state.currentModel) {
            const key = `${state.currentProvider}:${state.currentModel}`;
            seen.add(key);
            const providerInfo = getProviderInfo(state.currentProvider);
            unique.push({
                provider: state.currentProvider,
                model: state.currentModel,
                model_type: state.currentModelType,
                providerName: providerInfo ? providerInfo.name : state.currentProvider,
                icon: providerInfo ? providerInfo.icon : ''
            });
        }

        // 2. Add saved configs from state
        if (state.savedConfigs && state.savedConfigs.length > 0) {
            for (const conf of state.savedConfigs) {
                if (!conf.model) continue; // Skip generic parent provider settings (no model)

                const key = `${conf.provider}:${conf.model}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    const providerInfo = getProviderInfo(conf.provider);
                    unique.push({
                        provider: conf.provider,
                        model: conf.model,
                        model_type: null, // model_type not stored in user_api_keys
                        providerName: providerInfo ? providerInfo.name : conf.provider,
                        icon: providerInfo ? providerInfo.icon : ''
                    });
                }
            }
        }

        // 3. Then add models from session history if available
        if (window.Sessions && window.Sessions.allSessions) {
            const sessions = window.Sessions.allSessions;
            for (const s of sessions) {
                if (s.provider && s.model) {
                    const key = `${s.provider}:${s.model}`;
                    if (!seen.has(key)) {
                        seen.add(key);
                        const providerInfo = getProviderInfo(s.provider);
                        unique.push({
                            provider: s.provider,
                            model: s.model,
                            model_type: s.model_type,
                            providerName: providerInfo ? providerInfo.name : s.provider,
                            icon: providerInfo ? providerInfo.icon : ''
                        });
                    }
                }
                if (unique.length >= 10) break; // Increased limit to show more configured models
            }
        }

        console.log('[ModelSelector] Final unique models:', unique.length);
        return unique;
    }

    /**
     * Helper to get provider info
     */
    function getProviderInfo(id) {
        const p = PROVIDERS.find(p => p.id === id);
        if (p) return p;

        // Fallbacks for legacy/other providers
        if (id === 'anthropic') return { name: 'Anthropic', icon: 'https://upload.wikimedia.org/wikipedia/commons/7/78/Anthropic_logo.svg' };
        if (id === 'openai') return { name: 'OpenAI', icon: 'https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg' };

        // Generic fallback
        if (id === 'llama_cpp') return { name: 'Llama Cpp', icon: 'https://github.com/ggerganov/llama.cpp/raw/master/media/llama.cpp.png' };
        return { name: id, icon: 'https://uxwing.com/wp-content/themes/uxwing/download/web-app-development/api-icon.png' };
    }

    /**
     * Switch to a model from history (quick switch using cached credentials)
     */
    async function selectModelFromHistory(providerId, modelId) {
        // Don't switch if already on this model
        if (isCurrent(providerId, modelId)) {
            closeDropdown();
            return;
        }

        try {
            // Find model_type from history if possible
            let modelType = null;
            if (window.Sessions && window.Sessions.allSessions) {
                const session = window.Sessions.allSessions.find(s => s.provider === providerId && s.model === modelId);
                if (session) modelType = session.model_type;
            }

            // Get auth token for authenticated request
            const token = AppConfig.getAuthToken();

            // Show loading state
            if (elements.headerModelLabel) {
                elements.headerModelLabel.textContent = 'Switching...';
            }

            // Use the new quick-switch endpoint that fetches stored credentials automatically
            const response = await fetch(AppConfig.getApiUrl('/api/provider/switch-quick'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    provider: providerId,
                    model: modelId,
                    model_type: modelType
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.detail || 'Failed to switch provider';
                throw new Error(errorMessage);
            }

            // Update state
            updateCurrentModel(providerId, modelId, modelType);
            closeDropdown();

            // Show success notification
            if (window.Modals && window.Modals.toast) {
                window.Modals.toast(`Switched to ${modelId}`, 'success');
            }

            // Reconnect WebSocket to use new agent (faster than full page reload)
            if (typeof WebSocketManager !== 'undefined' && WebSocketManager.close) {
                console.log('[ModelSelector] Reconnecting WebSocket for new model...');
                WebSocketManager.close();
                setTimeout(() => {
                    WebSocketManager.init();
                    // Reload tools list to reflect new capabilities
                    if (typeof Tools !== 'undefined' && Tools.loadTools) {
                        Tools.loadTools();
                    }
                }, 300);
            } else {
                // Fallback: reload page if WebSocket manager not available
                window.location.reload();
            }

        } catch (e) {
            console.error('[ModelSelector] Failed to switch model:', e.message);

            // Restore the label
            if (elements.headerModelLabel) {
                elements.headerModelLabel.textContent = state.currentModel || 'Select Model';
            }

            // Show error toast instead of silently redirecting
            if (window.Modals && window.Modals.toast) {
                window.Modals.toast(e.message, 'error');
            } else {
                alert(e.message);
            }

            // Only redirect to setup if there's a credentials issue
            if (e.message.includes('No saved API key') || e.message.includes('No saved endpoint')) {
                setTimeout(() => {
                    window.location.href = `/setup.html?provider=${providerId}&model=${modelId}`;
                }, 1500);
            }
        }
    }

    /**
     * Select provider and redirect to setup page for model configuration
     * (Legacy function kept if needed)
     */
    function selectProviderAndRedirect(providerId) {
        closeDropdown();
        window.location.href = `/setup.html?provider=${providerId}`;
    }

    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Agentry dropdown toggle
        if (elements.agentryBtn) {
            elements.agentryBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleDropdown();
            });
        }

        // Go to settings button
        if (elements.gotoSettings) {
            elements.gotoSettings.addEventListener('click', (e) => {
                e.stopPropagation();
                closeDropdown();
                window.location.href = '/setup.html?step=model';
            });
        }

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (elements.agentryDropdown && !elements.agentryDropdown.contains(e.target)) {
                closeDropdown();
            }
        });

        // Close on ESC key
        // Config Modal Events
        if (elements.configCloseBtn) {
            elements.configCloseBtn.addEventListener('click', closeProviderConfig);
        }
        if (elements.configModalOverlay) {
            elements.configModalOverlay.addEventListener('click', (e) => {
                if (e.target === elements.configModalOverlay) closeProviderConfig();
            });
        }
        if (elements.configSaveBtn) {
            elements.configSaveBtn.addEventListener('click', saveProviderConfig);
        }

        // Saved Models Modal Events
        if (elements.savedModelsCloseBtn) {
            elements.savedModelsCloseBtn.addEventListener('click', closeSavedModelsModal);
        }
        if (elements.savedModelsModalOverlay) {
            elements.savedModelsModalOverlay.addEventListener('click', (e) => {
                if (e.target === elements.savedModelsModalOverlay) closeSavedModelsModal();
            });
        }
    }

    /**
     * Open Provider Config Modal
     */
    async function openProviderConfig(providerId, modelId) {
        if (!elements.configModalOverlay) return;

        closeDropdown(); // Close the dropdown behind it

        elements.configModalOverlay.classList.add('active');
        if (elements.configEditor) {
            elements.configEditor.value = 'Loading...';
            elements.configEditor.disabled = true;
        }
        if (elements.configSaveBtn) elements.configSaveBtn.disabled = true;

        try {
            const token = AppConfig.getAuthToken();
            const response = await fetch(AppConfig.getApiUrl(`/api/provider/config/${providerId}/${encodeURIComponent(modelId)}`), {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (response.ok) {
                const config = await response.json();
                if (elements.configEditor) {
                    elements.configEditor.value = JSON.stringify(config, null, 2);
                    elements.configEditor.disabled = false;
                    elements.configEditor.focus();
                }
                if (elements.configSaveBtn) elements.configSaveBtn.disabled = false;
            } else {
                throw new Error('Failed to load config');
            }
        } catch (e) {
            console.error('Failed to load provider config:', e);
            if (elements.configEditor) elements.configEditor.value = `Error: ${e.message}`;
        }
    }

    /**
     * Close Provider Config Modal
     */
    function closeProviderConfig() {
        if (elements.configModalOverlay) {
            elements.configModalOverlay.classList.remove('active');
        }
        if (elements.configError) elements.configError.style.display = 'none';
    }

    /**
     * Open Saved Models Modal
     */
    function openSavedModelsModal() {
        if (!elements.savedModelsModalOverlay) return;

        // Refresh the list
        renderSavedModelsList();

        elements.savedModelsModalOverlay.classList.add('active');
    }

    /**
     * Close Saved Models Modal
     */
    function closeSavedModelsModal() {
        if (elements.savedModelsModalOverlay) {
            elements.savedModelsModalOverlay.classList.remove('active');
        }
    }

    /**
     * Render the list inside Saved Models Modal
     */
    function renderSavedModelsList() {
        if (!elements.savedModelsList) return;

        const saved = (state.savedConfigs || []).filter(c => c.model);

        if (saved.length === 0) {
            elements.savedModelsList.innerHTML = `<div class="provider-popup-empty" style="text-align:center; padding: 20px; color: var(--text-muted);">No saved models configuration</div>`;
            return;
        }

        let html = '';
        saved.forEach(c => {
            const info = getProviderInfo(c.provider);
            // Re-use rendering logic, but maybe with slightly different container class
            const active = isCurrent(c.provider, c.model);
            const providerName = info ? info.name : c.provider;
            const icon = info ? info.icon : '';

            html += `
                <div class="provider-popup-item ${active ? 'active' : ''}" 
                     data-provider-id="${c.provider}" 
                     data-model-id="${c.model}"
                     style="margin-bottom: 4px;">
                    <div class="provider-popup-item-icon">
                        <img src="${icon}" alt="${providerName}" style="width: 100%; height: 100%; object-fit: contain;" onerror="this.style.display='none'">
                    </div>
                    <div class="provider-popup-item-info">
                        <div class="provider-popup-item-name">${c.model}</div>
                        <div class="provider-popup-item-model">${providerName}</div>
                    </div>
                    <div class="provider-popup-item-actions" style="display: flex; align-items: center; gap: 8px;">
                         ${active ? `
                        <span style="font-size: 11px; color: var(--accent); margin-right: 4px;">Active</span>` : ''}
                        
                        <button class="saved-model-use-btn" 
                                style="background: var(--accent); color: white; border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600; cursor: pointer;">
                            Use
                        </button>
                        
                        <button class="provider-edit-btn" style="background: none; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 4px; display: flex;" title="Edit Configuration">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="provider-delete-btn" style="background: none; border: none; color: inherit; opacity: 0.6; cursor: pointer; padding: 4px; display: flex;" title="Delete Configuration">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                <line x1="10" y1="11" x2="10" y2="17"></line>
                                <line x1="14" y1="11" x2="14" y2="17"></line>
                            </svg>
                        </button>
                    </div>
                </div>
             `;
        });

        elements.savedModelsList.innerHTML = html;

        // Modal Event Listeners
        elements.savedModelsList.querySelectorAll('.provider-popup-item').forEach(item => {
            // Main click (optional, maybe selecting row does nothing or highlight?)
            // Let's make "Use" button the primary action

            const useBtn = item.querySelector('.saved-model-use-btn');
            if (useBtn) {
                useBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const providerId = item.dataset.providerId;
                    const modelId = item.dataset.modelId;
                    closeSavedModelsModal();
                    selectModelFromHistory(providerId, modelId);
                });
            }

            const editBtn = item.querySelector('.provider-edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    // Close saved modal temporarily? Or open config on top?
                    // Config modal has higher z-index usually, or we can close this one.
                    closeSavedModelsModal();
                    openProviderConfig(item.dataset.providerId, item.dataset.modelId);
                });
            }

            const deleteBtn = item.querySelector('.provider-delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const providerId = item.dataset.providerId;
                    const modelId = item.dataset.modelId;

                    // We need to handle delete inside modal context (refresh list after delete)
                    if (!confirm(`Are you sure you want to delete the configuration for ${modelId}?`)) return;

                    try {
                        const token = AppConfig.getAuthToken();
                        const response = await fetch(AppConfig.getApiUrl(`/api/provider/config/${providerId}/${encodeURIComponent(modelId)}`), {
                            method: 'DELETE',
                            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                        });

                        if (response.ok) {
                            if (window.Modals && window.Modals.toast) window.Modals.toast(`Deleted ${modelId}`, 'success');
                            await fetchSavedConfigs(); // Refresh state
                            renderSavedModelsList(); // Re-render modal list

                            // If it was current, sync
                            if (isCurrent(providerId, modelId)) {
                                syncCurrentModel();
                            }
                        } else {
                            alert("Failed to delete");
                        }
                    } catch (err) {
                        console.error(err);
                    }
                });
            }
        });
    }

    /**
     * Save Provider Config
     */
    async function saveProviderConfig() {
        if (!elements.configEditor) return;

        try {
            const configText = elements.configEditor.value;
            let configJson;
            try {
                configJson = JSON.parse(configText);
            } catch (e) {
                throw new Error('Invalid JSON format');
            }

            // Basic validation
            if (!configJson.provider || !configJson.model) {
                throw new Error('JSON must contain "provider" and "model" fields');
            }

            elements.configSaveBtn.textContent = 'Saving...';
            elements.configSaveBtn.disabled = true;

            const token = AppConfig.getAuthToken();
            const response = await fetch(AppConfig.getApiUrl('/api/provider/configure'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify(configJson)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to save config');
            }

            // Success
            if (window.Modals && window.Modals.toast) {
                window.Modals.toast('Configuration saved successfully', 'success');
            }

            closeProviderConfig();

            // If we edited the current model, we might need to refresh
            if (isCurrent(configJson.provider, configJson.model)) {
                // Trigger a resync or soft reload
                syncCurrentModel();
                // If it was an API key change, we might want to reload the page or reconnect WS
                // For now, syncCurrentModel just updates UI text.
            }

            // Refresh dropdown in case names changed (unlikely with this tool but still)
            renderProviderPopup();

        } catch (e) {
            console.error('Failed to save config:', e);
            if (elements.configError) {
                elements.configError.textContent = e.message;
                elements.configError.style.display = 'block';
            }
            alert(e.message); // Fallback
        } finally {
            if (elements.configSaveBtn) {
                elements.configSaveBtn.textContent = 'Save Changes';
                elements.configSaveBtn.disabled = false;
            }
        }
    }

    /**
     * Fetch saved configurations from API
     */
    async function fetchSavedConfigs() {
        try {
            const token = AppConfig.getAuthToken();
            const response = await fetch(AppConfig.getApiUrl('/api/provider/saved'), {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (response.ok) {
                const data = await response.json();
                state.savedConfigs = data.configs || [];
                console.log('[ModelSelector] Loaded saved configs:', state.savedConfigs.length);
            }
        } catch (e) {
            console.error('[ModelSelector] Failed to fetch saved configs:', e);
        }
    }

    /**
     * Delete a provider configuration
     */
    async function deleteProviderConfig(providerId, modelId) {
        // Confirm deletion
        if (!confirm(`Are you sure you want to delete the configuration for ${modelId}?`)) {
            return;
        }

        try {
            const token = AppConfig.getAuthToken();
            const response = await fetch(AppConfig.getApiUrl(`/api/provider/config/${providerId}/${encodeURIComponent(modelId)}`), {
                method: 'DELETE',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (response.ok) {
                if (window.Modals && window.Modals.toast) {
                    window.Modals.toast(`Deleted configuration for ${modelId}`, 'success');
                }

                // Refresh saved configs and re-render
                await fetchSavedConfigs();
                renderProviderPopup();

                // If deleted model was current, maybe we should sync
                if (isCurrent(providerId, modelId)) {
                    syncCurrentModel();
                }
            } else {
                throw new Error('Failed to delete configuration');
            }
        } catch (e) {
            console.error('[ModelSelector] Failed to delete config:', e);
            if (window.Modals && window.Modals.toast) {
                window.Modals.toast(e.message, 'error');
            }
        }
    }

    /**
     * Toggle dropdown
     */
    function toggleDropdown() {
        state.isOpen = !state.isOpen;
        if (state.isOpen) {
            // Re-render when opening to show latest history
            renderProviderPopup();
        }
        if (elements.agentryDropdown) {
            elements.agentryDropdown.classList.toggle('open', state.isOpen);
        }
    }

    /**
     * Close dropdown
     */
    function closeDropdown() {
        state.isOpen = false;
        if (elements.agentryDropdown) {
            elements.agentryDropdown.classList.remove('open');
        }
    }

    /**
     * Get human readable name for a model ID
     */
    function getModelName(id) {
        for (const p of PROVIDERS) {
            const m = p.models.find(m => m.id === id);
            if (m) return m.name;
        }
        return id;
    }

    /**
     * Sync UI with current backend state
     */
    async function syncCurrentModel() {
        try {
            // Get auth token for authenticated request
            const token = AppConfig.getAuthToken();
            console.log('[ModelSelector] Syncing model, token present:', !!token);

            const response = await fetch(AppConfig.getApiUrl('/api/provider/current'), {
                headers: token ? {
                    'Authorization': `Bearer ${token}`
                } : {}
            });

            console.log('[ModelSelector] API response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('[ModelSelector] API response data:', data);

                if (data.config) {
                    state.currentModel = data.config.model;
                    state.currentProvider = data.config.provider;
                    state.currentModelType = data.config.model_type;

                    // Sync to localStorage
                    localStorage.setItem('agentry-active-model', state.currentModel);
                    localStorage.setItem('agentry-active-provider', state.currentProvider);
                    if (state.currentModelType) {
                        localStorage.setItem('agentry-active-model-type', state.currentModelType);
                    }
                    console.log('[ModelSelector] Synced current model:', state.currentProvider, state.currentModel);
                } else {
                    console.warn('[ModelSelector] No config in API response, using localStorage');
                    loadFromLocalStorage();
                }
            } else {
                console.warn('[ModelSelector] API returned', response.status, '- falling back to localStorage');
                loadFromLocalStorage();
            }
        } catch (e) {
            console.error('[ModelSelector] Failed to sync current model', e);
            loadFromLocalStorage();
        }

        // Update header model label
        if (elements.headerModelLabel) {
            elements.headerModelLabel.textContent = state.currentModel || 'Select Model';
        }

        // Re-render popup to show active state
        renderProviderPopup();
    }

    /**
     * Load model from localStorage (no hardcoded fallback)
     */
    function loadFromLocalStorage() {
        const savedModel = localStorage.getItem('agentry-active-model');
        const savedProvider = localStorage.getItem('agentry-active-provider');
        const savedModelType = localStorage.getItem('agentry-active-model-type');

        if (savedProvider && savedModel) {
            state.currentModel = savedModel;
            state.currentProvider = savedProvider;
            state.currentModelType = savedModelType;
            console.log('[ModelSelector] Loaded from localStorage:', state.currentProvider, state.currentModel);
        } else {
            // No saved config - leave as current state (initial defaults)
            console.log('[ModelSelector] No localStorage config found, using initial state');
        }
    }

    /**
     * Update model display from external source
     */
    function updateCurrentModel(provider, model, modelType = null) {
        state.currentProvider = provider;
        state.currentModel = model;
        state.currentModelType = modelType;

        localStorage.setItem('agentry-active-provider', provider);
        localStorage.setItem('agentry-active-model', model);
        if (modelType) {
            localStorage.setItem('agentry-active-model-type', modelType);
        }

        if (elements.headerModelLabel) {
            elements.headerModelLabel.textContent = model;
        }

        renderProviderPopup();
    }

    /**
     * Refresh the popup (call when sessions change)
     */
    function refresh() {
        console.log('[ModelSelector] Refreshing popup with latest session data...');
        renderProviderPopup();
    }

    return {
        init,
        PROVIDERS,
        updateCurrentModel,
        syncCurrentModel,
        refresh
    };
})();

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    ModelSelector.init();
});
window.ModelSelector = ModelSelector;
