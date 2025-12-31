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
        try {
            const response = await API.get('/api/sessions');
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

        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    },

    /**
     * Render sessions list
     */
    render(sessions) {
        const container = DOM.byId('sessions-container');
        if (!container) return;

        container.innerHTML = '';

        if (!sessions || sessions.length === 0) {
            const searchInput = DOM.byId('search-chats-input');
            const isSearching = searchInput && searchInput.value.trim().length > 0;
            const emptyMessage = isSearching ? 'No matching chats found' : 'No previous chats';
            container.innerHTML = `<p style="color: var(--text-secondary); font-size: 13px; text-align: center; padding: 20px;">${emptyMessage}</p>`;
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

            item.innerHTML = `
                <div class="session-title">${DOM.escapeHtml(session.title || 'Untitled Chat')}</div>
                <div class="session-date">${dateStr}, ${timeStr} · ${session.message_count || 0} turns</div>
                <button class="session-delete" title="Delete session">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        <line x1="10" y1="11" x2="10" y2="17"/>
                        <line x1="14" y1="11" x2="14" y2="17"/>
                    </svg>
                </button>
            `;

            // Click to load session
            DOM.on(item, 'click', (e) => {
                if (!e.target.closest('.session-delete')) {
                    this.loadSession(session.id);
                }
            });

            // Delete button
            const deleteBtn = item.querySelector('.session-delete');
            DOM.on(deleteBtn, 'click', (e) => {
                e.stopPropagation();
                this.delete(session.id);
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
        window.history.pushState({}, '', `/chat?session=${sessionId}`);

        // Update active state
        DOM.$$('.session-item').forEach(item => {
            DOM.toggleClass(item, 'active', item.dataset.sessionId === sessionId);
        });

        // Request session load via WebSocket
        if (WebSocketManager.ws && WebSocketManager.ws.readyState === WebSocket.OPEN) {
            WebSocketManager.send({ type: 'load_session', session_id: sessionId });
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
            window.history.pushState({}, '', `/chat?session=${response.session.id}`);

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
                window.history.pushState({}, '', '/chat');
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
