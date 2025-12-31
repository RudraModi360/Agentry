/**
 * AGENTRY UI - Modals Component
 * Handles all modal dialogs (approval, search, MCP, media gallery)
 */

const Modals = {
    // Approval modal state
    approvalTimeoutId: null,
    approvalCountdown: 120,

    /**
     * Initialize modals
     */
    init() {
        this.initSearch();
        this.initMCP();
        this.initMediaGallery();

        // Global ESC handler
        DOM.on(document, 'keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAll();
            }
        });

        AppConfig.log('Modals', 'Initialized');
    },

    /**
     * Close all modals
     */
    closeAll() {
        this.hideApproval();
        this.hideSearch();
        this.hideMCP();
        this.hideMediaGallery();
    },

    // ==================== Approval Modal ====================

    /**
     * Show tool approval modal
     */
    showApproval(toolName, args) {
        const overlay = DOM.byId('approval-modal-overlay');
        const toolNameEl = DOM.byId('approval-tool-name');
        const argsEl = DOM.byId('approval-args');
        const timeoutEl = DOM.byId('approval-timeout');
        const approveBtn = DOM.byId('approval-approve-btn');
        const denyBtn = DOM.byId('approval-deny-btn');

        if (!overlay) return;

        toolNameEl.textContent = `🔧 ${toolName}`;
        argsEl.textContent = JSON.stringify(args, null, 2);

        overlay.classList.add('active');

        // Start countdown
        this.approvalCountdown = AppConfig.tools.approvalTimeout / 1000;
        this.updateApprovalCountdown(timeoutEl);

        this.approvalTimeoutId = setInterval(() => {
            this.approvalCountdown--;
            this.updateApprovalCountdown(timeoutEl);
            if (this.approvalCountdown <= 0) {
                clearInterval(this.approvalTimeoutId);
                this.respondApproval(false);
            }
        }, 1000);

        // Button handlers
        const newApproveBtn = approveBtn.cloneNode(true);
        approveBtn.parentNode.replaceChild(newApproveBtn, approveBtn);
        DOM.on(newApproveBtn, 'click', () => this.respondApproval(true));

        const newDenyBtn = denyBtn.cloneNode(true);
        denyBtn.parentNode.replaceChild(newDenyBtn, denyBtn);
        DOM.on(newDenyBtn, 'click', () => this.respondApproval(false));
    },

    /**
     * Update countdown display
     */
    updateApprovalCountdown(el) {
        if (el) {
            el.textContent = `Auto-deny in ${this.approvalCountdown}s`;
        }
    },

    /**
     * Respond to approval request
     */
    respondApproval(approved) {
        if (this.approvalTimeoutId) {
            clearInterval(this.approvalTimeoutId);
            this.approvalTimeoutId = null;
        }

        WebSocketManager.sendApprovalResponse(approved);
        this.hideApproval();
    },

    /**
     * Hide approval modal
     */
    hideApproval() {
        const overlay = DOM.byId('approval-modal-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }

        if (this.approvalTimeoutId) {
            clearInterval(this.approvalTimeoutId);
            this.approvalTimeoutId = null;
        }
    },

    // ==================== Search Modal ====================

    /**
     * Initialize search modal
     */
    initSearch() {
        const overlay = DOM.byId('search-modal-overlay');
        const toggleBtn = DOM.byId('search-toggle-btn');
        const input = DOM.byId('modal-search-input');

        if (!overlay || !toggleBtn) return;

        DOM.on(toggleBtn, 'click', () => this.showSearch());

        DOM.on(overlay, 'click', (e) => {
            if (e.target === overlay) this.hideSearch();
        });

        // Cmd/Ctrl+K shortcut
        DOM.on(document, 'keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                if (overlay.classList.contains('active')) {
                    this.hideSearch();
                } else {
                    this.showSearch();
                }
            }
        });

        // Search input handler
        if (input) {
            let searchTimeout;
            DOM.on(input, 'input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => this.performSearch(input.value), 300);
            });
        }
    },

    /**
     * Show search modal
     */
    showSearch() {
        const overlay = DOM.byId('search-modal-overlay');
        const input = DOM.byId('modal-search-input');

        if (overlay) {
            overlay.classList.add('active');
            setTimeout(() => input?.focus(), 50);
            this.renderSearchResults(App.state.allSessions || []);
        }
    },

    /**
     * Hide search modal
     */
    hideSearch() {
        const overlay = DOM.byId('search-modal-overlay');
        const input = DOM.byId('modal-search-input');

        if (overlay) {
            overlay.classList.remove('active');
        }
        if (input) {
            input.value = '';
        }
    },

    /**
     * Perform search
     */
    async performSearch(query) {
        query = query.trim();

        if (!query) {
            this.renderSearchResults(App.state.allSessions || []);
            return;
        }

        try {
            const response = await API.get('/api/sessions/search', { q: query });
            this.renderSearchResults(response.sessions || [], true);
        } catch (error) {
            // Fallback to local search
            const filtered = (App.state.allSessions || []).filter(s =>
                (s.title || 'Untitled Chat').toLowerCase().includes(query.toLowerCase())
            );
            this.renderSearchResults(filtered);
        }
    },

    /**
     * Render search results
     */
    renderSearchResults(sessions, isSearch = false) {
        const list = DOM.byId('modal-sessions-list');
        if (!list) return;

        list.innerHTML = '';

        if (sessions.length === 0) {
            list.innerHTML = `<div class="modal-no-results">
                <p>${isSearch ? 'No matching chats found' : 'No recent chats'}</p>
            </div>`;
            return;
        }

        sessions.forEach(session => {
            const date = new Date(session.updated_at || session.created_at);
            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            const item = DOM.create('div', { class: 'modal-session-item' });
            item.innerHTML = `
                <div class="modal-session-icon">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </div>
                <div class="modal-session-info">
                    <div class="modal-session-title">${DOM.escapeHtml(session.title || 'Untitled Chat')}</div>
                    <div class="modal-session-meta">
                        <span>${dateStr}</span>
                        <span>·</span>
                        <span>${session.message_count || 0} turns</span>
                        ${isSearch && session.score > 200 ? '<span class="modal-match-badge">High Match</span>' : ''}
                    </div>
                    ${session.snippet ? `<div class="modal-session-snippet">${DOM.escapeHtml(session.snippet)}</div>` : ''}
                </div>
            `;

            DOM.on(item, 'click', () => {
                App.loadSession(session.id);
                this.hideSearch();
            });

            list.appendChild(item);
        });
    },

    // ==================== MCP Config Modal ====================

    /**
     * Initialize MCP modal
     */
    initMCP() {
        const overlay = DOM.byId('mcp-modal-overlay');
        const configBtn = DOM.byId('mcp-config-btn');
        const closeBtn = DOM.byId('mcp-modal-close-btn');
        const saveBtn = DOM.byId('mcp-save-btn');
        const refreshBtn = DOM.byId('mcp-refresh-btn');

        if (configBtn) {
            DOM.on(configBtn, 'click', () => this.showMCP());
        }

        if (overlay) {
            DOM.on(overlay, 'click', (e) => {
                if (e.target === overlay) this.hideMCP();
            });
        }

        if (closeBtn) {
            DOM.on(closeBtn, 'click', () => this.hideMCP());
        }

        if (saveBtn) {
            DOM.on(saveBtn, 'click', () => this.saveMCPConfig());
        }

        if (refreshBtn) {
            DOM.on(refreshBtn, 'click', () => this.refreshMCPStatus());
        }
    },

    /**
     * Show MCP modal
     */
    async showMCP() {
        const overlay = DOM.byId('mcp-modal-overlay');
        const editor = DOM.byId('mcp-json-editor');

        if (!overlay) return;

        overlay.classList.add('active');

        // Load current config and status
        try {
            const [configRes, statusRes] = await Promise.all([
                API.get('/api/mcp/config'),
                API.get('/api/mcp/status')
            ]);

            const config = configRes.config || { mcpServers: {} };
            const mcpServers = config.mcpServers || {};
            const statuses = statusRes.statuses || {};

            if (editor) {
                editor.value = JSON.stringify(config, null, 2);
            }

            // Map to array
            const serverList = Object.keys(mcpServers).map(name => {
                let count = '?';
                if (window.Tools && window.Tools.mcpServers && window.Tools.mcpServers[name]) {
                    count = window.Tools.mcpServers[name].length;
                }
                return {
                    name: name,
                    status: statuses[name] || 'disconnected',
                    tool_count: count
                };
            });

            this.renderMCPServerList(serverList);

        } catch (error) {
            console.error('Failed to load MCP config:', error);
            if (editor) {
                editor.value = '{\n  "mcpServers": {}\n}';
            }
            this.renderMCPServerList([]);
        }
    },

    /**
     * Hide MCP modal
     */
    hideMCP() {
        const overlay = DOM.byId('mcp-modal-overlay');
        if (overlay) overlay.classList.remove('active');
    },

    /**
     * Save MCP configuration
     */
    async saveMCPConfig() {
        const editor = DOM.byId('mcp-json-editor');
        const saveBtn = DOM.byId('mcp-save-btn');

        if (!editor || !saveBtn) return;

        try {
            const config = JSON.parse(editor.value);

            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';

            await API.post('/api/mcp/config', { config });

            // Refresh list
            await this.refreshMCPStatus();

            saveBtn.textContent = 'Saved!';
            setTimeout(() => {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save Configuration';
            }, 2000);

        } catch (error) {
            console.error('Failed to save MCP config:', error);
            alert('Invalid JSON or save failed: ' + error.message);
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Configuration';
        }
    },

    /**
     * Refresh MCP status
     */
    async refreshMCPStatus() {
        const refreshBtn = DOM.byId('mcp-refresh-btn');

        try {
            if (refreshBtn) {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '<span class="spinner"></span> Refreshing...';
            }

            const [configRes, statusRes] = await Promise.all([
                API.get('/api/mcp/config'),
                API.get('/api/mcp/status')
            ]);

            const mcpServers = (configRes.config || {}).mcpServers || {};
            const statuses = statusRes.statuses || {};

            const serverList = Object.keys(mcpServers).map(name => {
                let count = '?';
                if (window.Tools && window.Tools.mcpServers && window.Tools.mcpServers[name]) {
                    count = window.Tools.mcpServers[name].length;
                }
                return {
                    name: name,
                    status: statuses[name] || 'disconnected',
                    tool_count: count
                };
            });

            this.renderMCPServerList(serverList);

        } catch (error) {
            console.error('Failed to refresh MCP:', error);
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <polyline points="1 20 1 14 7 14"></polyline>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                    </svg>
                    Refresh Status
                `;
            }
        }
    },

    /**
     * Render MCP server list
     */
    renderMCPServerList(servers) {
        const list = DOM.byId('mcp-server-list');
        if (!list) return;

        if (!servers || servers.length === 0) {
            list.innerHTML = '<div class="mcp-no-servers">No MCP servers configured</div>';
            return;
        }

        list.innerHTML = servers.map(server => `
            <div class="mcp-server-item">
                <div class="mcp-server-status ${server.status || 'disconnected'}"></div>
                <div class="mcp-server-info">
                    <div class="mcp-server-name">${DOM.escapeHtml(server.name)}</div>
                    <div class="mcp-server-tools">${server.tool_count || 0} tools</div>
                </div>
            </div>
        `).join('');
    },

    // ==================== Media Gallery Modal ====================

    /**
     * Initialize media gallery modal
     */
    initMediaGallery() {
        const overlay = DOM.byId('media-gallery-overlay');
        const viewAllBtn = DOM.byId('media-view-all-btn');
        const sidebarMediaBtn = DOM.byId('media-gallery-btn');
        const closeBtn = DOM.byId('media-gallery-close-btn');

        if (viewAllBtn) {
            DOM.on(viewAllBtn, 'click', () => this.showMediaGallery());
        }

        if (sidebarMediaBtn) {
            DOM.on(sidebarMediaBtn, 'click', () => this.showMediaGallery());
        }

        if (overlay) {
            DOM.on(overlay, 'click', (e) => {
                if (e.target === overlay) this.hideMediaGallery();
            });
        }

        if (closeBtn) {
            DOM.on(closeBtn, 'click', () => this.hideMediaGallery());
        }
    },

    /**
     * Show media gallery
     */
    showMediaGallery() {
        const overlay = DOM.byId('media-gallery-overlay');
        if (overlay) {
            overlay.classList.add('active');
            if (typeof MediaLibrary !== 'undefined') {
                MediaLibrary.renderGallery();
            }
        }
    },

    /**
     * Hide media gallery
     */
    hideMediaGallery() {
        const overlay = DOM.byId('media-gallery-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Modals;
}
window.Modals = Modals;
