/**
 * AGENTRY UI - Model Selector Component
 * Handles the dual-view dropdown for selecting providers and models.
 */

const ModelSelector = (function () {
    'use strict';

    // Model Data
    const PROVIDERS = [
        {
            id: 'groq',
            name: 'Groq',
            icon: 'https://github.com/groq.png',
            models: [
                { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B' },
                { id: 'llama-3.1-70b-versatile', name: 'Llama 3.1 70B' },
                { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7b' }
            ]
        },
        {
            id: 'gemini',
            name: 'Gemini',
            icon: 'https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg',
            models: [
                { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
                { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' },
                { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' }
            ]
        },
        {
            id: 'azure',
            name: 'Azure',
            icon: 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Microsoft_Azure.svg',
            models: [
                { id: 'gpt-4o', name: 'GPT-4o' },
                { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
                { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet' }
            ]
        },
        {
            id: 'ollama',
            name: 'Ollama',
            icon: 'https://github.com/ollama.png',
            models: [
                { id: 'llama3.2', name: 'Llama 3.2' },
                { id: 'llama3.1', name: 'Llama 3.1' },
                { id: 'phi3', name: 'Phi-3' },
                { id: 'mistral', name: 'Mistral' }
            ]
        }
    ];

    // State
    const state = {
        isOpen: false,
        selectedProvider: null,
        currentModel: 'gpt-4o'
    };

    // DOM Elements
    const elements = {
        selectorBtn: null,
        dropdown: null,
        providerList: null,
        modelList: null,
        modelOptions: null,
        backBtn: null,
        providerLabel: null,
        currentModelText: null
    };

    /**
     * Initialize the component
     */
    function init() {
        cacheElements();
        if (!elements.selectorBtn) return;

        renderProviders();
        setupEventListeners();

        // Initial UI sync
        syncCurrentModel();
    }

    /**
     * Cache DOM elements
     */
    function cacheElements() {
        elements.selectorBtn = document.getElementById('model-selector-btn');
        elements.dropdown = document.getElementById('model-dropdown');
        elements.providerList = document.getElementById('provider-list');
        elements.modelList = document.getElementById('model-list');
        elements.modelOptions = document.getElementById('model-options');
        elements.backBtn = document.getElementById('back-to-providers');
        elements.providerLabel = document.getElementById('selected-provider-label');
        elements.currentModelText = document.getElementById('current-model-display');
    }

    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Toggle Dropdown
        elements.selectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown();
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (state.isOpen && !elements.dropdown.contains(e.target) && !elements.selectorBtn.contains(e.target)) {
                closeDropdown();
            }
        });

        // Back to providers view
        if (elements.backBtn) {
            elements.backBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showProviderView();
            });
        }
    }

    /**
     * Toggle dropdown open/closed
     */
    function toggleDropdown() {
        state.isOpen = !state.isOpen;
        elements.dropdown.classList.toggle('open', state.isOpen);
        elements.selectorBtn.classList.toggle('open', state.isOpen);

        if (state.isOpen) {
            showProviderView(); // Reset to provider view when opening
        }
    }

    /**
     * Close dropdown
     */
    function closeDropdown() {
        state.isOpen = false;
        elements.dropdown.classList.remove('open');
        elements.selectorBtn.classList.remove('open');
    }

    /**
     * Render the provider selection view
     */
    function renderProviders() {
        if (!elements.providerList) return;

        elements.providerList.innerHTML = PROVIDERS.map(provider => `
            <div class="provider-option" data-provider-id="${provider.id}">
                <div class="provider-item-content">
                    <img src="${provider.icon}" alt="${provider.name}" class="provider-icon-mini">
                    <span>${provider.name}</span>
                </div>
                <svg viewBox="0 0 24 24" class="provider-chevron" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6" />
                </svg>
            </div>
        `).join('');

        // Attach clicks
        elements.providerList.querySelectorAll('.provider-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                const providerId = opt.dataset.providerId;
                showModelView(providerId);
            });
        });
    }

    /**
     * Show Provider View
     */
    function showProviderView() {
        elements.providerList.style.display = 'block';
        elements.modelList.style.display = 'none';
        elements.providerList.classList.add('view-fade-in');
    }

    /**
     * Show Model View for a specific provider
     */
    function showModelView(providerId) {
        const provider = PROVIDERS.find(p => p.id === providerId);
        if (!provider) return;

        state.selectedProvider = provider;
        elements.providerLabel.textContent = provider.name;

        // Render models
        elements.modelOptions.innerHTML = provider.models.map(model => `
            <div class="model-option ${state.currentModel === model.id ? 'selected' : ''}" data-model-id="${model.id}">
                ${model.name}
            </div>
        `).join('');

        // Attach clicks
        elements.modelOptions.querySelectorAll('.model-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                selectModel(opt.dataset.modelId);
            });
        });

        elements.providerList.style.display = 'none';
        elements.modelList.style.display = 'block';
        elements.modelList.classList.add('view-fade-in');
    }

    /**
     * Select a model and update backend
     */
    async function selectModel(modelId) {
        state.currentModel = modelId;
        elements.currentModelText.textContent = getModelName(modelId);

        // Close dropdown
        closeDropdown();

        // Update Backend
        if (window.App && window.App.saveAgentType) {
            // Reusing saveAgentType or similar API call logic
            // In a real app, this would be API.post('/api/model/switch', ...)
            try {
                const config = {
                    provider: state.selectedProvider.id,
                    model: modelId
                };

                // Show loading in main header if needed
                console.log('[ModelSelector] Switching to:', config);

                // Call the actual backend update
                await API.post('/api/agent/configure', {
                    provider: config.provider,
                    model: config.model
                });

                // Reset WebSocket to apply changes
                WebSocketManager.close();
                setTimeout(() => WebSocketManager.init(), 500);

            } catch (err) {
                console.error('[ModelSelector] Failed to switch model:', err);
            }
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
    function syncCurrentModel() {
        // This will be called after App.loadUserInfo completes 
        // Or we can check storage
        const currentModel = localStorage.getItem('agentry-active-model') || 'gpt-4o';
        state.currentModel = currentModel;
        if (elements.currentModelText) {
            elements.currentModelText.textContent = getModelName(currentModel);
        }
    }

    return {
        init,
        PROVIDERS
    };
})();

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    ModelSelector.init();
});
window.ModelSelector = ModelSelector;
