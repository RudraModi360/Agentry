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

    // State - populated from API/localStorage
    const state = {
        isOpen: false,
        currentModel: null,
        currentProvider: null,
        currentModelType: null
    };

    // DOM Elements cache
    const elements = {};

    /**
     * Get provider info by ID
     */
    function getProviderInfo(id) {
        return PROVIDERS.find(p => p.id === id) || { name: id, icon: '' };
    }

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
                    <button class="provider-popup-item-edit" data-provider-id="${item.provider}" data-model-id="${item.model}" title="Edit config">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
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

        // Attach click handlers for model selection (clicking on the item but not the edit button)
        elements.providerPopupList.querySelectorAll('.provider-popup-item:not(.manage-item)').forEach(item => {
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking the edit button
                if (e.target.closest('.provider-popup-item-edit')) return;
                e.stopPropagation();
                const providerId = item.dataset.providerId;
                const modelId = item.dataset.modelId;
                selectModelFromHistory(providerId, modelId);
            });
        });

        // Attach edit button handlers
        elements.providerPopupList.querySelectorAll('.provider-popup-item-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const providerId = btn.dataset.providerId;
                const modelId = btn.dataset.modelId;
                closeDropdown();
                // Open the manage models modal with the config editor
                openManageModelsModal();
                // Then open the config editor for this model
                setTimeout(() => openConfigEditor(providerId, modelId), 100);
            });
        });

        // Attach Manage Handler - opens the modal
        const manageBtn = document.getElementById('provider-manage-btn');
        if (manageBtn) {
            manageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                closeDropdown();
                openManageModelsModal();
            });
        }
    }

    /**
     * Open the Manage Models modal
     */
    function openManageModelsModal() {
        const overlay = document.getElementById('manage-models-overlay');
        if (overlay) {
            renderManageModelsList();
            overlay.classList.add('active');
        }
    }

    /**
     * Close the Manage Models modal
     */
    function closeManageModelsModal() {
        const overlay = document.getElementById('manage-models-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    /**
     * Render the list of models in the manage modal
     */
    function renderManageModelsList() {
        const listContainer = document.getElementById('manage-models-list');
        if (!listContainer) return;

        const recentModels = getRecentModelsFromHistory();

        if (recentModels.length === 0) {
            listContainer.innerHTML = `
                <div class="manage-models-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                    </svg>
                    <p>No previously used models</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = recentModels.map(item => `
            <div class="manage-model-item ${isCurrent(item.provider, item.model) ? 'current' : ''}" data-provider-id="${item.provider}" data-model-id="${item.model}">
                <div class="manage-model-icon">
                    <img src="${item.icon}" alt="${item.providerName}" onerror="this.style.display='none'">
                </div>
                <div class="manage-model-info">
                    <div class="manage-model-name">${item.model}</div>
                    <div class="manage-model-provider">${item.providerName}</div>
                </div>
                ${isCurrent(item.provider, item.model) ? '<span class="manage-model-badge">Current</span>' : ''}
                <div class="manage-model-actions">
                    <button class="manage-model-btn edit" data-provider-id="${item.provider}" data-model-id="${item.model}" title="Edit configuration">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="manage-model-btn delete" data-provider-id="${item.provider}" data-model-id="${item.model}" title="Remove from list">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        // Attach handlers
        listContainer.querySelectorAll('.manage-model-btn.edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const providerId = btn.dataset.providerId;
                const modelId = btn.dataset.modelId;
                openConfigEditor(providerId, modelId);
            });
        });

        listContainer.querySelectorAll('.manage-model-btn.delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const providerId = btn.dataset.providerId;
                const modelId = btn.dataset.modelId;
                deleteModelFromHistory(providerId, modelId);
            });
        });

        // Allow clicking on item to select it
        listContainer.querySelectorAll('.manage-model-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.manage-model-btn')) return;
                const providerId = item.dataset.providerId;
                const modelId = item.dataset.modelId;
                closeManageModelsModal();
                selectModelFromHistory(providerId, modelId);
            });
        });
    }

    // State for config editor
    const editorState = {
        currentProvider: null,
        currentModel: null,
        currentModelType: null
    };

    /**
     * Open the inline config editor for a model
     */
    async function openConfigEditor(providerId, modelId) {
        console.log('[ModelSelector] Opening config editor for:', providerId, modelId);

        editorState.currentProvider = providerId;
        editorState.currentModel = modelId;

        // Find model info
        const providerInfo = getProviderInfo(providerId);

        // Update modal title
        const titleText = document.getElementById('manage-models-title-text');
        if (titleText) {
            titleText.textContent = 'Edit Configuration';
        }

        // Populate model info header
        const modelInfoEl = document.getElementById('config-editor-model-info');
        if (modelInfoEl) {
            modelInfoEl.innerHTML = `
                <div class="model-icon">
                    <img src="${providerInfo.icon}" alt="${providerInfo.name}" onerror="this.style.display='none'">
                </div>
                <div class="model-details">
                    <div class="model-name">${modelId}</div>
                    <div class="model-provider">${providerInfo.name}</div>
                </div>
            `;
        }

        // Pre-fill model name
        const modelNameInput = document.getElementById('config-model-name');
        if (modelNameInput) {
            modelNameInput.value = modelId;
        }

        // Clear API key field (for security, we don't pre-fill API keys)
        const apiKeyInput = document.getElementById('config-api-key');
        if (apiKeyInput) {
            apiKeyInput.value = '';
        }

        // Show/hide endpoint field based on provider
        const endpointGroup = document.getElementById('config-endpoint-group');
        const endpointInput = document.getElementById('config-endpoint');

        // Fetch saved config to pre-fill
        try {
            const token = AppConfig.getAuthToken();
            const response = await fetch(AppConfig.getApiUrl(`/api/provider/saved/${providerId}`), {
                headers: {
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                }
            });

            if (response.ok) {
                const savedConfig = await response.json();

                if (savedConfig.api_key && apiKeyInput) {
                    apiKeyInput.value = savedConfig.api_key;
                    apiKeyInput.placeholder = '••••••••••••••••';
                }

                if (savedConfig.endpoint && endpointInput) {
                    endpointInput.value = savedConfig.endpoint;
                }
            }
        } catch (e) {
            console.warn('[ModelSelector] Could not fetch saved config:', e);
        }

        if (endpointGroup && endpointInput) {
            if (providerId === 'azure' || providerId === 'ollama') {
                endpointGroup.style.display = 'flex';
                if (!endpointInput.value) {
                    if (providerId === 'azure') {
                        endpointInput.placeholder = 'https://your-resource.openai.azure.com';
                    } else {
                        endpointInput.placeholder = 'http://localhost:11434';
                    }
                }
            } else {
                endpointGroup.style.display = 'none';
            }
        }

        // Clear messages
        const errorMsg = document.getElementById('config-error-message');
        const successMsg = document.getElementById('config-success-message');
        if (errorMsg) errorMsg.style.display = 'none';
        if (successMsg) successMsg.style.display = 'none';

        // Switch views
        document.getElementById('manage-models-list-view').style.display = 'none';
        document.getElementById('manage-models-edit-view').style.display = 'block';
        document.getElementById('manage-models-list-footer').style.display = 'none';
        document.getElementById('manage-models-edit-footer').style.display = 'flex';
    }

    /**
     * Close config editor and go back to list view
     */
    function closeConfigEditor() {
        // Reset title
        const titleText = document.getElementById('manage-models-title-text');
        if (titleText) {
            titleText.textContent = 'Manage Models';
        }

        // Switch views
        document.getElementById('manage-models-list-view').style.display = 'block';
        document.getElementById('manage-models-edit-view').style.display = 'none';
        document.getElementById('manage-models-list-footer').style.display = 'flex';
        document.getElementById('manage-models-edit-footer').style.display = 'none';

        // Clear editor state
        editorState.currentProvider = null;
        editorState.currentModel = null;
    }

    /**
     * Save the configuration from the editor
     */
    async function saveConfigFromEditor() {
        const providerId = editorState.currentProvider;
        const apiKey = document.getElementById('config-api-key').value.trim();
        const modelName = document.getElementById('config-model-name').value.trim();
        const endpoint = document.getElementById('config-endpoint')?.value.trim() || null;

        const errorMsg = document.getElementById('config-error-message');
        const successMsg = document.getElementById('config-success-message');
        const saveBtn = document.getElementById('config-save-btn');

        // Clear previous messages
        if (errorMsg) errorMsg.style.display = 'none';
        if (successMsg) successMsg.style.display = 'none';

        // Validation
        if (!modelName) {
            if (errorMsg) {
                errorMsg.textContent = 'Please enter a model/deployment name';
                errorMsg.style.display = 'block';
            }
            return;
        }

        // For Azure, endpoint is required
        if (providerId === 'azure' && !endpoint) {
            if (errorMsg) {
                errorMsg.textContent = 'Please enter the Azure endpoint URL';
                errorMsg.style.display = 'block';
            }
            return;
        }

        // Show loading state
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = `
                <svg class="spin" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"></circle>
                </svg>
                Saving...
            `;
        }

        try {
            const token = AppConfig.getAuthToken();

            const payload = {
                provider: providerId,
                model: modelName,
                mode: providerId === 'ollama' ? 'cloud' : null,
                api_key: apiKey || null,
                endpoint: endpoint,
                model_type: editorState.currentModelType || null
            };

            console.log('[ModelSelector] Saving config:', payload);

            const response = await fetch(AppConfig.getApiUrl('/api/provider/configure'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                // Success!
                if (successMsg) {
                    successMsg.textContent = 'Configuration saved successfully!';
                    successMsg.style.display = 'block';
                }

                // Update local state
                updateCurrentModel(providerId, modelName, editorState.currentModelType);

                // Show toast
                if (window.Modals && window.Modals.toast) {
                    window.Modals.toast('Configuration saved!', 'success');
                }

                // Close editor and modal after a short delay
                setTimeout(() => {
                    closeConfigEditor();
                    closeManageModelsModal();

                    // Reconnect WebSocket to use new config
                    if (typeof WebSocketManager !== 'undefined' && WebSocketManager.close) {
                        console.log('[ModelSelector] Reconnecting WebSocket for new config...');
                        WebSocketManager.close();
                        setTimeout(() => {
                            WebSocketManager.init();
                            if (typeof Tools !== 'undefined' && Tools.loadTools) {
                                Tools.loadTools();
                            }
                        }, 300);
                    }
                }, 1000);

            } else {
                // Error from server
                if (errorMsg) {
                    errorMsg.textContent = data.detail || 'Failed to save configuration';
                    errorMsg.style.display = 'block';
                }
            }
        } catch (e) {
            console.error('[ModelSelector] Error saving config:', e);
            if (errorMsg) {
                errorMsg.textContent = 'Connection error. Please try again.';
                errorMsg.style.display = 'block';
            }
        } finally {
            // Reset button
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Save Configuration
                `;
            }
        }
    }

    /**
     * Delete a model from history (removes from localStorage tracking)
     */
    async function deleteModelFromHistory(providerId, modelId) {
        // For now, we can try to call an API to remove saved credentials
        try {
            const token = AppConfig.getAuthToken();

            const response = await fetch(AppConfig.getApiUrl('/api/provider/saved/' + providerId), {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                }
            });

            if (response.ok) {
                if (window.Modals && window.Modals.toast) {
                    window.Modals.toast(`Removed ${modelId} configuration`, 'success');
                }
            }
        } catch (e) {
            console.warn('[ModelSelector] Could not delete from server:', e);
        }

        // Also clear from localStorage if it matches
        const savedProvider = localStorage.getItem('agentry-active-provider');
        const savedModel = localStorage.getItem('agentry-active-model');

        if (savedProvider === providerId && savedModel === modelId) {
            localStorage.removeItem('agentry-active-provider');
            localStorage.removeItem('agentry-active-model');
            localStorage.removeItem('agentry-active-model-type');
        }

        // Re-render the list
        renderManageModelsList();
        renderProviderPopup();
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
        console.log('[ModelSelector] Current state:', state.currentProvider, state.currentModel);

        const unique = [];
        const seen = new Set();

        // ALWAYS add current model first if it exists (regardless of session availability)
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
            console.log('[ModelSelector] Added current model:', state.currentProvider, state.currentModel);
        }

        // Then add models from session history if available
        if (window.Sessions && window.Sessions.allSessions) {
            const sessions = window.Sessions.allSessions;
            console.log('[ModelSelector] Processing', sessions.length, 'sessions');

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
                        console.log('[ModelSelector] Added history model:', s.provider, s.model);
                    }
                }
                if (unique.length >= 5) break;
            }
        } else {
            console.log('[ModelSelector] No sessions available yet, showing only current model');
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
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeDropdown();
                closeManageModelsModal();
            }
        });

        // Manage Models Modal close handlers
        const manageModelsOverlay = document.getElementById('manage-models-overlay');
        const manageModelsCloseBtn = document.getElementById('manage-models-close-btn');

        if (manageModelsOverlay) {
            manageModelsOverlay.addEventListener('click', (e) => {
                if (e.target === manageModelsOverlay) {
                    closeManageModelsModal();
                }
            });
        }

        if (manageModelsCloseBtn) {
            manageModelsCloseBtn.addEventListener('click', () => {
                closeManageModelsModal();
            });
        }

        // Add New Model button
        const addModelBtn = document.getElementById('manage-models-add-btn');
        if (addModelBtn) {
            addModelBtn.addEventListener('click', () => {
                closeManageModelsModal();
                window.location.href = '/setup.html';
            });
        }

        // Config Editor buttons
        const configEditorBack = document.getElementById('config-editor-back');
        const configCancelBtn = document.getElementById('config-cancel-btn');
        const configSaveBtn = document.getElementById('config-save-btn');
        const toggleApiKeyVisibility = document.getElementById('toggle-api-key-visibility');

        if (configEditorBack) {
            configEditorBack.addEventListener('click', () => {
                closeConfigEditor();
            });
        }

        if (configCancelBtn) {
            configCancelBtn.addEventListener('click', () => {
                closeConfigEditor();
            });
        }

        if (configSaveBtn) {
            configSaveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                saveConfigFromEditor();
            });
        }

        if (toggleApiKeyVisibility) {
            toggleApiKeyVisibility.addEventListener('click', () => {
                const apiKeyInput = document.getElementById('config-api-key');
                if (apiKeyInput) {
                    if (apiKeyInput.type === 'password') {
                        apiKeyInput.type = 'text';
                        toggleApiKeyVisibility.innerHTML = `
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                                <line x1="1" y1="1" x2="23" y2="23"></line>
                            </svg>
                        `;
                    } else {
                        apiKeyInput.type = 'password';
                        toggleApiKeyVisibility.innerHTML = `
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                        `;
                    }
                }
            });
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
        refresh,
        openManageModelsModal,
        closeManageModelsModal,
        openConfigEditor,
        closeConfigEditor
    };
})();

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    ModelSelector.init();
});
window.ModelSelector = ModelSelector;
