/**
 * ============================================================
 * AGENTRY UI - Main Application Entry Point
 * ============================================================
 * 
 * This file initializes all components and orchestrates the
 * application startup.
 * 
 * Load order in HTML:
 * 1. config.js           - Configuration
 * 2. utils/dom.js        - DOM utilities
 * 3. utils/api.js        - API utilities
 * 4. utils/storage.js    - Storage utilities
 * 5. components/theme.js - Theme management
 * 6. components/clock.js - Clock widget
 * 7. components/sidebar.js - Sidebar
 * 8. components/messages.js - Message rendering
 * 9. components/websocket.js - WebSocket connection
 * 10. components/modals.js - Modal dialogs
 * 11. components/tools.js - Tools popup
 * 12. components/sessions.js - Session management
 * 13. components/upload.js - Image upload
 * 14. main.js            - This file
 */

const App = {
    // Application state
    state: {
        isConnected: false,
        isProcessing: false,
        isAutoScrollEnabled: true,
        currentSessionId: null,
        allSessions: [],
        userInfo: null,
        ws: null
    },

    /**
     * Initialize the application
     */
    async init() {
        console.log('[Agentry] Initializing application...');

        // Check authentication
        if (!this.checkAuth()) return;

        // Initialize all components
        this.initComponents();

        // Load initial data
        await this.loadInitialData();

        // Setup global event listeners
        this.setupGlobalEvents();

        // Check URL for session parameter
        this.checkUrlSession();

        console.log('[Agentry] Application initialized');
    },

    /**
     * Check if user is authenticated
     */
    checkAuth() {
        const token = AppConfig.getAuthToken();
        if (!token) {
            window.location.href = AppConfig.auth.loginPath;
            return false;
        }
        return true;
    },

    /**
     * Initialize all components
     */
    initComponents() {
        // Theme (applies immediately in theme.js, init sets up listeners)
        Theme.init();

        // Clock widget
        Clock.init();

        // Sidebar
        Sidebar.init();

        // Messages
        Messages.init();

        // Modals
        Modals.init();

        // Profile Modal
        if (typeof ProfileModal !== 'undefined') {
            ProfileModal.init();
        }

        // Tools
        Tools.init();

        // Sessions
        Sessions.init();

        // Image upload
        ImageUpload.init();

        // Media Library & Gallery
        if (typeof Media !== 'undefined') {
            Media.init();
        }

        // Auto-correct
        AutoCorrect.init();

        // Agent type selector
        this.initAgentTypeSelector();

        // Message input
        this.initMessageInput();

        // Scroll behavior
        this.initScrollBehavior();
    },

    /**
     * Load initial data from API
     */
    async loadInitialData() {
        try {
            // Load user info
            await this.loadUserInfo();

            // Load sessions
            await Sessions.load();

            // Load tools
            await Tools.loadTools();

            // Connect WebSocket
            WebSocketManager.init();

        } catch (error) {
            console.error('[Agentry] Failed to load initial data:', error);
            if (error.isUnauthorized && error.isUnauthorized()) {
                Storage.remove(AppConfig.auth.tokenKey);
                window.location.href = AppConfig.auth.loginPath;
            }
        }
    },

    /**
     * Load user info
     */
    async loadUserInfo() {
        try {
            const response = await API.get('/api/auth/me');
            this.state.userInfo = response.user;

            // Update UI
            DOM.text('user-name', response.user?.username || 'User');
            const initial = (response.user?.username || 'U')[0].toUpperCase();
            DOM.text('user-avatar', initial);

            // Add click listener for profile modal
            const userSection = document.querySelector('.footer-section.user-section');
            if (userSection) {
                userSection.style.cursor = 'pointer';
                userSection.setAttribute('title', 'Click to edit profile');
                userSection.onclick = (e) => {
                    e.stopPropagation(); // Prevent bubbling
                    if (typeof ProfileModal !== 'undefined') {
                        ProfileModal.open();
                    }
                };
            }

            // Update provider info
            if (response.provider_config) {
                const provider = response.provider_config.provider;
                const model = response.provider_config.model || 'Default';

                // Sync with new ModelSelector component
                const modelDisplay = DOM.byId('current-model-display');
                if (modelDisplay) modelDisplay.textContent = model;

                // Update header model label (from ModelSelector logic)
                const headerModelLabel = DOM.byId('header-model-label');
                if (headerModelLabel) headerModelLabel.textContent = model;

                // Sync agent type from backend
                if (response.provider_config.agent_type) {
                    Storage.set(AppConfig.agents.storageKey, response.provider_config.agent_type);
                    this.updateAgentTypeUI(response.provider_config.agent_type);
                }
            }

        } catch (error) {
            console.error('[Agentry] Failed to load user info:', error);
            if (error.isUnauthorized && error.isUnauthorized()) {
                Storage.remove(AppConfig.auth.tokenKey);
                window.location.href = AppConfig.auth.loginPath;
            }
        }
    },



    /**
     * Load session (public method)
     */
    async loadSession(sessionId) {
        await Sessions.loadSession(sessionId);
    },

    /**
     * Load sessions (public method)
     */
    async loadSessions() {
        await Sessions.load();
    },

    /**
     * Check URL for session parameter
     */
    checkUrlSession() {
        const params = new URLSearchParams(window.location.search);
        const sessionId = params.get('session');

        if (sessionId) {
            Sessions.loadSession(sessionId);
        }
    },

    /**
     * Initialize agent type selector
     */
    initAgentTypeSelector() {
        const button = DOM.byId('agent-type-button');
        const dropdown = DOM.byId('agent-type-dropdown');
        const options = DOM.$$('.agent-type-option');

        // Load saved agent type
        const savedType = Storage.get(AppConfig.agents.storageKey, AppConfig.agents.default);
        this.updateAgentTypeUI(savedType);

        // Toggle dropdown
        if (button) {
            DOM.on(button, 'click', (e) => {
                e.stopPropagation();
                DOM.toggleClass(button, 'open');
                DOM.toggleClass(dropdown, 'open');
            });
        }

        // Close on outside click
        DOM.on(document, 'click', (e) => {
            if (!e.target.closest('.agent-type-selector')) {
                if (button) DOM.removeClass(button, 'open');
                if (dropdown) DOM.removeClass(dropdown, 'open');
            }
        });

        // Handle option click
        options.forEach(option => {
            DOM.on(option, 'click', async (e) => {
                e.stopPropagation(); // Prevent event from bubbling to button
                const type = option.dataset.agent;
                Storage.set(AppConfig.agents.storageKey, type);
                this.updateAgentTypeUI(type);

                // Save to backend
                await this.saveAgentType(type);

                if (button) DOM.removeClass(button, 'open');
                if (dropdown) DOM.removeClass(dropdown, 'open');
            });
        });
    },

    /**
     * Save agent type to backend
     */
    async saveAgentType(type, mode = 'solo', projectId = null) {
        try {
            await API.post('/api/agent-config', {
                agent_type: type,
                mode: mode,
                project_id: projectId
            });
            console.log(`[Agentry] Agent type saved: ${type}`);

            // Reload tools to reflect locked status
            if (typeof Tools !== 'undefined' && Tools.loadTools) {
                await Tools.loadTools();
            }

            // Reconnect WebSocket to ensure new agent is instantiated with correct type
            if (typeof WebSocketManager !== 'undefined') {
                console.log('[Agentry] Reconnecting WebSocket for new agent type...');
                WebSocketManager.close();
                setTimeout(() => WebSocketManager.init(), 500);
            }
        } catch (error) {
            console.error('[Agentry] Failed to save agent type:', error);
        }
    },

    /**
     * Update agent type UI
     */
    updateAgentTypeUI(type) {
        const config = AppConfig.agents.types[type];
        if (!config) return;

        DOM.text('agent-type-label', config.name);

        // Update selected state
        DOM.$$('.agent-type-option').forEach(opt => {
            DOM.toggleClass(opt, 'selected', opt.dataset.agent === type);
        });

        // Toggle feature visibility
        const mcpBtn = DOM.byId('mcp-config-btn');
        const toolsContainer = DOM.byId('tools-btn-container');
        const attachBtn = DOM.byId('attach-image-btn');

        if (mcpBtn) DOM.toggle(mcpBtn, config.features.mcp, 'flex');
        if (toolsContainer) DOM.toggle(toolsContainer, config.features.tools, 'flex');
        if (attachBtn) DOM.toggle(attachBtn, config.features.vision, 'flex');
    },

    /**
     * Initialize message input
     */
    initMessageInput() {
        const input = DOM.byId('message-input');
        const sendBtn = DOM.byId('send-btn');

        if (!input) return;

        // Initialize Input Editor
        if (typeof InputEditor !== 'undefined') {
            InputEditor.init();
        }

        // Send button click
        if (sendBtn) {
            DOM.on(sendBtn, 'click', () => this.sendMessage());
        }

        // Logout button
        const logoutBtn = DOM.byId('header-logout-btn');
        if (logoutBtn) {
            DOM.on(logoutBtn, 'click', async () => {
                try {
                    await API.post('/api/auth/logout');
                } catch (e) { }
                Storage.remove(AppConfig.auth.tokenKey);
                window.location.href = AppConfig.auth.loginPath;
            });
        }
    },

    /**
     * Send a message
     */
    async sendMessage() {
        // Use InputEditor if available, otherwise fallback (though HTML changed)
        let content = '';
        if (typeof InputEditor !== 'undefined') {
            content = InputEditor.getValue().trim();
        } else {
            const input = DOM.byId('message-input');
            content = input?.value.trim();
        }

        const images = ImageUpload.getImages();
        const hasImages = images.length > 0;

        if ((!content && !hasImages) || !this.state.isConnected || this.state.isProcessing) {
            return;
        }

        this.state.isProcessing = true;
        DOM.byId('send-btn').disabled = true;

        // Display user message
        Messages.addUserMessage(content, null, null, images);

        // Clear input
        if (typeof InputEditor !== 'undefined') {
            InputEditor.clear();
        } else {
            DOM.byId('message-input').value = '';
        }
        ImageUpload.clear();

        // Hide autocorrect button since input is now empty
        if (typeof AutoCorrect !== 'undefined' && AutoCorrect.updateButtonVisibility) {
            AutoCorrect.updateButtonVisibility();
        }

        // Show thinking spinner
        Messages.currentAssistantMessage = Messages.createAssistantMessage();
        Messages.currentAssistantText = '';

        // Create session if needed
        if (!this.state.currentSessionId) {
            try {
                const response = await API.post('/api/sessions');
                this.state.currentSessionId = response.session.id;
            } catch (error) {
                console.error('[Agentry] Failed to create session:', error);
                this.state.isProcessing = false;
                return;
            }
        }

        // Send via WebSocket
        WebSocketManager.sendMessage(content, images);
    },

    /**
     * Initialize scroll behavior
     */
    initScrollBehavior() {
        const container = DOM.byId('messages-container');
        const scrollBtn = DOM.byId('scroll-bottom-btn');

        if (!container || !scrollBtn) return;

        DOM.on(container, 'scroll', () => {
            const threshold = 100;
            const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold;

            if (isNearBottom) {
                this.state.isAutoScrollEnabled = true;
                scrollBtn.classList.remove('visible');
            } else {
                if (this.state.isAutoScrollEnabled) {
                    this.state.isAutoScrollEnabled = false;
                }
                scrollBtn.classList.add('visible');
            }
        });

        DOM.on(scrollBtn, 'click', () => {
            Messages.scrollToBottom(true);
        });
    },

    /**
     * Setup global event listeners
     */
    setupGlobalEvents() {
        // Handle browser back/forward
        window.addEventListener('popstate', () => {
            const params = new URLSearchParams(window.location.search);
            const sessionId = params.get('session');

            if (sessionId) {
                Sessions.loadSession(sessionId);
            } else {
                this.state.currentSessionId = null;
                Messages.clear();
            }
        });

        // Mobile menu button
        const menuBtn = DOM.byId('mobile-menu-btn');
        if (menuBtn) {
            DOM.on(menuBtn, 'click', () => Sidebar.toggleMobile());
        }
    }
};

// Initialize when DOM is ready
DOM.ready(() => {
    App.init();
});

// Expose globally for HTML onclick handlers
window.App = App;
window.deleteSession = (id) => Sessions.delete(id);
window.copyCodeBlock = (btn) => Messages.copyCodeBlock(btn);
window.copyTableBlock = (btn, id) => Messages.copyTableBlock?.(btn, id);

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = App;
}
