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
    function init() {
        console.log('[ModelSelector] Initializing...');
        cacheElements();
        console.log('[ModelSelector] Elements cached:', elements);
        renderProviderPopup();
        setupEventListeners();
        syncCurrentModel();
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
    function renderProviderPopup() {
        if (!elements.providerPopupList) return;

        elements.providerPopupList.innerHTML = PROVIDERS.map(provider => `
            <div class="provider-popup-item ${state.currentProvider === provider.id ? 'active' : ''}" data-provider-id="${provider.id}">
                <div class="provider-popup-item-icon">
                    <img src="${provider.icon}" alt="${provider.name}" onerror="this.style.display='none'">
                </div>
                <div class="provider-popup-item-info">
                    <div class="provider-popup-item-name">${provider.name}</div>
                    <div class="provider-popup-item-model">${provider.description}</div>
                </div>
                <svg class="provider-popup-item-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
        `).join('');

        // Attach click handlers - redirect to setup page for model selection
        elements.providerPopupList.querySelectorAll('.provider-popup-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const providerId = item.dataset.providerId;
                selectProviderAndRedirect(providerId);
            });
        });
    }

    /**
     * Select provider and redirect to setup page for model configuration
     */
    function selectProviderAndRedirect(providerId) {
        closeDropdown();
        // Redirect to setup page step 1 with the provider pre-selected
        // The setup page will handle the provider config workflow
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
    function syncCurrentModel() {
        const storedModel = localStorage.getItem('agentry-active-model') || 'claude-opus-4-5';
        const storedProvider = localStorage.getItem('agentry-active-provider') || 'anthropic';

        state.currentModel = storedModel;
        state.currentProvider = storedProvider;

        // Update header model label
        if (elements.headerModelLabel) {
            elements.headerModelLabel.textContent = storedModel;
        }

        // Re-render popup to show active state
        renderProviderPopup();
    }

    /**
     * Update model display from external source
     */
    function updateCurrentModel(provider, model) {
        state.currentProvider = provider;
        state.currentModel = model;

        localStorage.setItem('agentry-active-provider', provider);
        localStorage.setItem('agentry-active-model', model);

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
