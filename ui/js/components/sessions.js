/**
 * AGENTRY UI - Sessions Component
 * Handles session list and session management
 */

const Sessions = {
    allSessions: [],

    /**
     * Initialize sessions component
     */
    init() {
        this.setupEventListeners();
        AppConfig.log('Sessions', 'Initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const newChatBtn = DOM.byId('new-chat-btn');
        if (newChatBtn) {
            DOM.on(newChatBtn, 'click', () => this.createNew());
        }

        // Search input in sidebar (if exists)
        const searchInput = DOM.byId('search-chats-input');
        if (searchInput) {
            DOM.on(searchInput, 'input', () => {
                const query = searchInput.value.trim().toLowerCase();
                if (query) {
                    const filtered = this.allSessions.filter(s =>
                        (s.title || 'Untitled Chat').toLowerCase().includes(query)
                    );
                    this.render(filtered);
                } else {
                    this.render(this.allSessions);
                }
            });
        }
    },


    /**
     * Load sessions from server
     */
    async load() {
        console.log('[Sessions] Loading sessions...');
        try {
            const response = await API.get('/api/sessions');
            console.log('[Sessions] Loaded:', response.sessions ? response.sessions.length : 0);
            this.allSessions = response.sessions || [];
            App.state.allSessions = this.allSessions;

            // Check for search filter
            const searchInput = DOM.byId('search-chats-input');
            const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

            if (query) {
                const filtered = this.allSessions.filter(s =>
                    (s.title || 'Untitled Chat').toLowerCase().includes(query)
                );
                this.render(filtered);
            } else {
                this.render(this.allSessions);
            }

            // Refresh ModelSelector to show recent models from history
            if (typeof ModelSelector !== 'undefined' && ModelSelector.refresh) {
                ModelSelector.refresh();
            }

        } catch (error) {
            console.error('[Sessions] Failed to load sessions:', error);
        }
    },

    /**
     * Render sessions list
     */
    render(sessions) {
        const container = DOM.byId('sessions-container');
        const header = DOM.byId('sessions-header');

        if (!container) {
            console.error('[Sessions] Container not found!');
            return;
        }

        // Force visibility
        container.style.display = 'block';
        if (header) header.style.display = 'block';

        container.innerHTML = '';
        console.log('[Sessions] Rendering', sessions ? sessions.length : 0, 'sessions');


        if (!sessions || sessions.length === 0) {
            const searchInput = DOM.byId('search-chats-input');
            const isSearching = searchInput && searchInput.value.trim().length > 0;
            const emptyMessage = isSearching ? 'No matching chats found' : 'No previous chats';
            container.innerHTML = `<div style="color: rgba(255,255,255,0.4); font-size: 13px; text-align: center; padding: 20px;">${emptyMessage}</div>`;
            return;
        }

        sessions.forEach(session => {
            const item = DOM.create('div', { class: 'session-item' });
            if (session.id === App.state.currentSessionId) {
                item.classList.add('active');
            }
            item.dataset.sessionId = session.id;

            const date = new Date(session.updated_at || session.created_at);
            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
            const turnCount = session.message_count || 0;

            item.innerHTML = `
                <div class="session-info">
                    <div class="session-title">${DOM.escapeHtml(session.title || 'Untitled Chat')}</div>
                    <div class="session-meta">${dateStr}, ${timeStr} · ${turnCount} turns</div>
                </div>
                <button class="session-menu-btn" title="More options">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                        <circle cx="12" cy="5" r="1.5"/>
                        <circle cx="12" cy="12" r="1.5"/>
                        <circle cx="12" cy="19" r="1.5"/>
                    </svg>
                </button>
            `;

            // Click to load session
            DOM.on(item, 'click', (e) => {
                if (!e.target.closest('.session-menu-btn')) {
                    this.loadSession(session.id);
                }
            });

            // Menu button (for now, just delete - can expand to dropdown later)
            const menuBtn = item.querySelector('.session-menu-btn');
            DOM.on(menuBtn, 'click', (e) => {
                e.stopPropagation();
                // For now, just delete - can add dropdown menu later
                if (confirm('Delete this chat?')) {
                    this.delete(session.id);
                }
            });

            container.appendChild(item);
        });
    },

    /**
     * Load a specific session
     */
    async loadSession(sessionId) {
        if (App.state.isProcessing) return;

        App.state.currentSessionId = sessionId;

        // Update URL
        window.history.pushState({}, '', `/chat.html?session=${sessionId}`);

        // Update active state
        DOM.$$('.session-item').forEach(item => {
            DOM.toggleClass(item, 'active', item.dataset.sessionId === sessionId);
        });

        // Request session load via WebSocket
        if (WebSocketManager.ws && WebSocketManager.ws.readyState === WebSocket.OPEN) {
            console.log('[Sessions] Requesting load for session:', sessionId);
            WebSocketManager.send({ type: 'load_session', session_id: sessionId });
        } else {
            console.warn('[Sessions] WebSocket not ready, will retry load for:', sessionId);
            setTimeout(() => this.loadSession(sessionId), 500);
        }

        // Close mobile sidebar
        Sidebar.closeMobile();
    },

    /**
     * Create new session
     */
    async createNew() {
        try {
            const response = await API.post('/api/sessions');
            App.state.currentSessionId = response.session.id;
            Messages.clear();
            await this.load();

            // Update URL
            window.history.pushState({}, '', `/chat.html?session=${response.session.id}`);

        } catch (error) {
            console.error('Failed to create session:', error);
        }
    },

    /**
     * Delete session
     */
    async delete(sessionId) {
        if (!confirm('Are you sure you want to delete this chat? This cannot be undone.')) {
            return;
        }

        try {
            await API.delete(`/api/sessions/${sessionId}`);

            // If we deleted the current session, clear it
            if (sessionId === App.state.currentSessionId) {
                App.state.currentSessionId = null;
                Messages.clear();
                window.history.pushState({}, '', '/chat.html');
            }

            await this.load();

        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    },

    /**
     * Get session by ID
     */
    getById(sessionId) {
        return this.allSessions.find(s => s.id === sessionId);
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Sessions;
}
window.Sessions = Sessions;
