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
        }
    ];

    // State
    const state = {
        isOpen: false,
        currentModel: 'claude-opus-4-5',
        currentProvider: 'anthropic'
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
    }

    /**
     * Render provider items in the popup
     */
    /**
     * Render provider items in the popup based on history
     */
    function renderProviderPopup() {
        if (!elements.providerPopupList) return;

        const recentModels = getRecentModelsFromHistory();
        let html = '';

        if (recentModels.length === 0) {
            html += `<div class="provider-popup-empty" style="padding: 12px; font-size: 13px; color: var(--text-secondary); text-align: center;">No recent models</div>`;
        } else {
            html += recentModels.map(item => `
                <div class="provider-popup-item ${isCurrent(item.provider, item.model) ? 'active' : ''}" 
                     data-provider-id="${item.provider}" 
                     data-model-id="${item.model}">
                    <div class="provider-popup-item-icon">
                        <img src="${item.icon}" alt="${item.providerName}" style="width: 100%; height: 100%; object-fit: contain;" onerror="this.style.display='none'">
                    </div>
                    <div class="provider-popup-item-info">
                        <div class="provider-popup-item-name">${item.model}</div>
                        <div class="provider-popup-item-model">${item.providerName}</div>
                    </div>
                    ${isCurrent(item.provider, item.model) ? `
                    <svg class="provider-popup-item-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>` : ''}
                </div>
            `).join('');
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
                    <div class="provider-popup-item-name">Manage Models</div>
                </div>
            </div>
        `;

        elements.providerPopupList.innerHTML = html;

        // Attach click handlers
        elements.providerPopupList.querySelectorAll('.provider-popup-item:not(.manage-item)').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const providerId = item.dataset.providerId;
                const modelId = item.dataset.modelId;
                selectModelFromHistory(providerId, modelId);
            });
        });

        // Attach Manage Handler
        const manageBtn = document.getElementById('provider-manage-btn');
        if (manageBtn) {
            manageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeDropdown();
                window.location.href = '/setup';
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
        if (!window.Sessions || !window.Sessions.allSessions) return [];

        const sessions = window.Sessions.allSessions;
        const unique = [];
        const seen = new Set();

        // Add current model first if it exists
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
            if (unique.length >= 5) break;
        }
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
        return { name: id, icon: 'https://uxwing.com/wp-content/themes/uxwing/download/web-app-development/api-icon.png' };
    }

    /**
     * Switch to a model from history
     */
    async function selectModelFromHistory(providerId, modelId) {
        // Here we would normally switch the provider/model via API
        // For now, let's redirect to setup with pre-fill or just update local state if we had a quick-switch API
        // Since the requirement is "manage options directly redirect to setup", 
        // implies clicking a history item should probably SWITCH to it immediately.
        // But we don't have a direct "switch" API endpoint in this file yet (it's in server.py PUT /api/provider/switch)

        // Let's call the switch API
        try {
            // Find model_type from history if possible
            let modelType = null;
            if (window.Sessions && window.Sessions.allSessions) {
                const session = window.Sessions.allSessions.find(s => s.provider === providerId && s.model === modelId);
                if (session) modelType = session.model_type;
            }

            const response = await fetch('/api/provider/switch', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: providerId,
                    model: modelId,
                    model_type: modelType
                })
            });

            if (!response.ok) {
                throw new Error('Failed to switch provider');
            }

            // Update state
            updateCurrentModel(providerId, modelId, modelType);
            closeDropdown();

            // Reload page to ensure backend state is clean? Or just let it be.
            // A reload is safer to ensure agent is re-initialized on backend
            window.location.reload();

        } catch (e) {
            console.error('Failed to switch model', e);
            window.location.href = `/setup?provider=${providerId}&model=${modelId}`;
        }
    }

    /**
     * Select provider and redirect to setup page for model configuration
     * (Legacy function kept if needed)
     */
    function selectProviderAndRedirect(providerId) {
        closeDropdown();
        window.location.href = `/setup?provider=${providerId}`;
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
                window.location.href = '/setup?step=model';
            });
        }

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (elements.agentryDropdown && !elements.agentryDropdown.contains(e.target)) {
                closeDropdown();
            }
        });

        // Close on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeDropdown();
            }
        });
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
            const response = await fetch('/api/provider/current');
            if (response.ok) {
                const data = await response.json();
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
                }
            } else {
                // Fallback to localStorage if API fails
                state.currentModel = localStorage.getItem('agentry-active-model') || 'llama3-70b';
                state.currentProvider = localStorage.getItem('agentry-active-provider') || 'groq';
                state.currentModelType = localStorage.getItem('agentry-active-model-type');
            }
        } catch (e) {
            console.error('[ModelSelector] Failed to sync current model', e);
            state.currentModel = localStorage.getItem('agentry-active-model') || 'llama3-70b';
            state.currentProvider = localStorage.getItem('agentry-active-provider') || 'groq';
            state.currentModelType = localStorage.getItem('agentry-active-model-type');
        }

        // Update header model label
        if (elements.headerModelLabel) {
            elements.headerModelLabel.textContent = state.currentModel;
        }

        // Re-render popup to show active state
        renderProviderPopup();
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

    return {
        init,
        PROVIDERS,
        updateCurrentModel,
        syncCurrentModel
    };
})();

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    ModelSelector.init();
});
window.ModelSelector = ModelSelector;
