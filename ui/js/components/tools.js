/**
 * AGENTRY UI - Tools Component
 * Handles tools popup and tool management
 */

const Tools = {
    availableTools: [],
    mcpServers: {},
    mcpServerStatuses: {},
    disabledTools: new Set(),
    isPopupOpen: false,
    toolsLocked: false,

    /**
     * Initialize tools component
     */
    init() {
        this.loadDisabledTools();
        this.setupEventListeners();
        this.loadTools();

        AppConfig.log('Tools', 'Initialized');
    },

    /**
     * Load disabled tools from storage
     */
    loadDisabledTools() {
        const saved = Storage.get(AppConfig.tools.disabledStorageKey, []);
        this.disabledTools = new Set(saved);
    },

    /**
     * Save disabled tools to storage and backend
     */
    saveDisabledTools() {
        Storage.set(AppConfig.tools.disabledStorageKey, Array.from(this.disabledTools));
        this.saveDisabledToBackend();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const toolsBtn = DOM.byId('tools-btn');
        const toolsPopup = DOM.byId('tools-popup');
        const closeBtn = DOM.byId('tools-popup-close');

        if (toolsBtn) {
            DOM.on(toolsBtn, 'click', (e) => {
                e.stopPropagation();
                this.togglePopup();
            });
        }

        if (closeBtn) {
            DOM.on(closeBtn, 'click', () => this.closePopup());
        }

        // Close on outside click
        DOM.on(document, 'click', (e) => {
            if (this.isPopupOpen && !e.target.closest('.tools-btn-container')) {
                this.closePopup();
            }
        });
    },

    /**
     * Toggle tools popup
     */
    togglePopup() {
        if (this.isPopupOpen) {
            this.closePopup();
        } else {
            this.openPopup();
        }
    },

    /**
     * Open tools popup
     */
    openPopup() {
        const popup = DOM.byId('tools-popup');
        const btn = DOM.byId('tools-btn');

        if (popup) {
            popup.classList.add('active');
            this.isPopupOpen = true;
        }

        if (btn) {
            btn.classList.add('active');
        }

        this.renderToolsList();
    },

    /**
     * Close tools popup
     */
    closePopup() {
        const popup = DOM.byId('tools-popup');
        const btn = DOM.byId('tools-btn');

        if (popup) {
            popup.classList.remove('active');
            this.isPopupOpen = false;
        }

        if (btn) {
            btn.classList.remove('active');
        }
    },

    /**
     * Load available tools from server
     */
    async loadTools() {
        try {
            const [toolsRes, statusRes] = await Promise.all([
                API.get('/api/tools'),
                API.get('/api/mcp/status')
            ]);

            // API returns { builtin: [...], mcp: {...}, tools_locked: boolean }
            this.availableTools = toolsRes.builtin || [];
            this.mcpServers = toolsRes.mcp || {};
            this.toolsLocked = toolsRes.tools_locked === true;
            this.mcpServerStatuses = statusRes.statuses || {};

            // Load disabled tools from backend
            await this.loadDisabledFromBackend();

            this.updateHeaderBadge();

        } catch (error) {
            console.error('Failed to load tools:', error);
        }
    },

    /**
     * Load disabled tools from backend
     */
    async loadDisabledFromBackend() {
        try {
            const response = await API.get('/api/tools/disabled');
            if (response.disabled_tools) {
                this.disabledTools = new Set(response.disabled_tools);
                this.saveDisabledTools();
            }
        } catch (error) {
            // Ignore errors, use localStorage
        }
    },

    /**
     * Save disabled tools to backend
     */
    async saveDisabledToBackend() {
        try {
            await API.post('/api/tools/disabled', {
                disabled_tools: Array.from(this.disabledTools)
            });
        } catch (error) {
            console.error('Failed to sync disabled tools:', error);
        }
    },

    /**
     * Update MCP status badge in header
     */
    updateHeaderBadge() {
        const badge = DOM.byId('mcp-header-status');
        if (!badge) return;

        const serverNames = Object.keys(this.mcpServers);
        if (serverNames.length === 0) {
            badge.className = 'mcp-status-badge none';
            return;
        }

        const statuses = Object.values(this.mcpServerStatuses);
        if (statuses.every(s => s === 'connected')) {
            badge.className = 'mcp-status-badge connected';
        } else if (statuses.some(s => s === 'connecting')) {
            badge.className = 'mcp-status-badge connecting';
        } else {
            badge.className = 'mcp-status-badge disconnected';
        }
    },

    /**
     * Render tools list in popup
     */
    renderToolsList() {
        const content = DOM.byId('tools-popup-content');
        if (!content) return;

        let html = '';
        const builtinCount = this.availableTools.length;
        const enabledBuiltinCount = this.availableTools.filter(t => !this.disabledTools.has(`builtin:${t.name}`)).length;

        let mcpToolsCount = 0;
        let enabledMcpCount = 0;
        Object.keys(this.mcpServers).forEach(server => {
            const tools = this.mcpServers[server] || [];
            mcpToolsCount += tools.length;
            enabledMcpCount += tools.filter(t => !this.disabledTools.has(`mcp:${server}:${t.name}`)).length;
        });

        const totalCount = builtinCount + mcpToolsCount;
        const totalEnabled = enabledBuiltinCount + enabledMcpCount;

        // Media Upload Section
        html += `
            <div class="tools-section-static-header">Upload Media</div>
            <div class="upload-media-item" id="merged-upload-btn">
                <div class="tool-item-icon">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <circle cx="8.5" cy="8.5" r="1.5"></circle>
                        <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                </div>
                <div class="upload-media-item-info">
                    <div class="upload-media-item-name">Attach Images</div>
                    <div class="upload-media-item-desc">Upload photos from your device</div>
                </div>
            </div>
        `;

        // Tools Header with enabled count
        html += `
            <div class="tools-section-static-header">
                <span>tools</span>
                <span class="tools-section-count">${totalEnabled}</span>
            </div>
        `;

        // Built-in Tools Section (Collapsible)
        if (builtinCount > 0) {
            const builtinExpanded = localStorage.getItem('builtin-tools-expanded') === 'true';
            html += `
                <div class="tools-section-group ${builtinExpanded ? 'expanded' : ''}" id="builtin-tools-group">
                    <div class="tools-section-header-expandable" data-group="builtin-tools-group">
                        <svg class="tools-section-expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                        </svg>
                        <span class="tools-section-title">Built-in Tools</span>
                        <span class="tools-section-count">${enabledBuiltinCount}</span>
                        <div class="tools-toggle-wrapper" onclick="event.stopPropagation()">
                            <label class="tools-switch">
                                <input type="checkbox" id="builtin-tools-toggle" ${this.isBuiltinEnabled() ? 'checked' : ''}>
                                <span class="tools-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="tools-section-content">
                        <div class="tools-list" id="builtin-tools-list">
                            ${this.renderBuiltinTools()}
                        </div>
                    </div>
                </div>
            `;
        }

        // MCP Tools Section (Collapsible)
        const serverNames = Object.keys(this.mcpServers);
        if (serverNames.length > 0) {
            const mcpExpanded = localStorage.getItem('mcp-tools-expanded') === 'true';
            html += `
                <div class="tools-section-group ${mcpExpanded ? 'expanded' : ''}" id="mcp-tools-group">
                    <div class="tools-section-header-expandable" data-group="mcp-tools-group">
                        <svg class="tools-section-expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                        <span class="tools-section-title">MCP Tools</span>
                        <span class="tools-section-count">${enabledMcpCount}</span>
                        <div class="tools-toggle-wrapper" onclick="event.stopPropagation()">
                            <label class="tools-switch">
                                <input type="checkbox" id="mcp-section-toggle" ${this.isMcpEnabled() ? 'checked' : ''}>
                                <span class="tools-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="tools-section-content">
                        <div class="tools-list" id="mcp-tools-list">
                            ${this.renderMcpTools()}
                        </div>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="tools-section-group" id="mcp-tools-group">
                    <div class="tools-section-header-expandable" data-group="mcp-tools-group">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                        <span class="tools-section-title">MCP Tools</span>
                        <span class="tools-section-count">0</span>
                        <svg class="tools-section-expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </div>
                    <div class="tools-section-content">
                        <div class="tools-empty">No MCP servers configured</div>
                    </div>
                </div>
            `;
        }

        content.innerHTML = html;

        // Add event listeners
        this.attachSectionToggleListeners();
        this.attachSectionExpandListeners();
        this.attachUploadListener();
    },

    /**
     * Helper to create tool item HTML matching original design
     */
    createToolItemHTML(tool, type) {
        const toolId = type === 'mcp' ? `mcp:${tool.server}:${tool.name}` : `builtin:${tool.name}`;
        const isDisabled = this.disabledTools.has(toolId);
        const isLocked = this.toolsLocked;

        return `
            <div class="tool-item ${isDisabled ? 'disabled' : ''} ${isLocked ? 'locked' : ''}">
                <div class="tool-item-icon ${type === 'mcp' ? 'mcp' : ''}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
                    </svg>
                </div>
                <div class="tool-item-info">
                    <div class="tool-item-name">${DOM.escapeHtml(tool.name)} ${isLocked ? '<span class="locked-badge" style="font-size: 10px; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 10px; margin-left: 8px; vertical-align: middle; border: 1px solid rgba(255,255,255,0.2);">Locked</span>' : ''}</div>
                    <div class="tool-item-desc">${DOM.escapeHtml(tool.description || 'No description')}</div>
                </div>
                <label class="tool-toggle ${isLocked ? 'disabled' : ''}">
                    <input type="checkbox" data-tool="${toolId}" ${!isDisabled ? 'checked' : ''} ${isLocked ? 'disabled' : ''}>
                    <span class="tool-toggle-slider"></span>
                </label>
            </div>
        `;
    },

    /**
     * Render built-in tools list
     */
    renderBuiltinTools() {
        if (this.availableTools.length === 0) {
            return '<div class="tools-empty">No built-in tools</div>';
        }
        return this.availableTools.map(tool => this.createToolItemHTML(tool, 'builtin')).join('');
    },

    /**
     * Render MCP tools list
     */
    renderMcpTools() {
        const serverNames = Object.keys(this.mcpServers);
        if (serverNames.length === 0) {
            return '<div class="tools-empty">No MCP servers configured</div>';
        }

        let html = '';
        serverNames.forEach(serverName => {
            const tools = this.mcpServers[serverName] || [];

            const status = this.mcpServerStatuses[serverName] || 'disconnected';
            const serverExpanded = localStorage.getItem(`mcp-server-${serverName}-expanded`) === 'true';
            const enabledCount = tools.filter(t => !this.disabledTools.has(`mcp:${serverName}:${t.name}`)).length;
            const allDisabled = tools.length > 0 && tools.every(t => this.disabledTools.has(`mcp:${serverName}:${t.name}`));

            html += `
                <div class="mcp-server-group ${serverExpanded ? 'expanded' : ''} ${allDisabled ? 'disabled-server' : ''}" data-server="${DOM.escapeHtml(serverName)}">
                    <div class="mcp-server-group-header">
                        <svg class="mcp-server-expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                        <div class="mcp-server-status ${status}"></div>
                        <span class="mcp-server-name">${DOM.escapeHtml(serverName)}</span>
                        <span class="mcp-server-tools-count">${enabledCount} / ${tools.length}</span>
                        <div class="tools-toggle-wrapper" onclick="event.stopPropagation()">
                            <label class="tools-switch">
                                <input type="checkbox" class="mcp-server-toggle" data-server="${DOM.escapeHtml(serverName)}" ${!allDisabled ? 'checked' : ''}>
                                <span class="tools-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="mcp-server-tools">
                        <div class="tools-list">
                            ${tools.length > 0 ? tools.map(tool => this.createToolItemHTML({ ...tool, server: serverName }, 'mcp')).join('') : '<div class="tools-empty">No tools</div>'}
                        </div>
                    </div>
                </div>
            `;
        });

        return html || '<div class="tools-empty">No tools available</div>';
    },

    /**
     * Check if builtin section is enabled (at least one tool enabled)
     */
    isBuiltinEnabled() {
        if (this.availableTools.length === 0) return true;
        return this.availableTools.some(t => !this.disabledTools.has(`builtin:${t.name}`));
    },

    /**
     * Check if MCP section is enabled (at least one tool enabled across all servers)
     */
    isMcpEnabled() {
        const serverNames = Object.keys(this.mcpServers);
        let totalTools = 0;
        let enabledCount = 0;

        serverNames.forEach(server => {
            const tools = this.mcpServers[server] || [];
            totalTools += tools.length;
            enabledCount += tools.filter(t => !this.disabledTools.has(`mcp:${server}:${t.name}`)).length;
        });

        if (totalTools === 0) return true;
        return enabledCount > 0;
    },

    /**
     * Attach section toggle listeners (enable/disable all in section)
     */
    attachSectionToggleListeners() {
        const builtinToggle = DOM.byId('builtin-tools-toggle');
        if (builtinToggle) {
            DOM.on(builtinToggle, 'change', (e) => {
                e.stopPropagation();
                const enable = builtinToggle.checked;
                this.availableTools.forEach(t => {
                    const toolId = `builtin:${t.name}`;
                    if (enable) {
                        this.disabledTools.delete(toolId);
                    } else {
                        this.disabledTools.add(toolId);
                    }
                });
                this.saveDisabledTools();
                this.renderToolsList();
            });
        }

        const mcpToggle = DOM.byId('mcp-section-toggle');
        if (mcpToggle) {
            DOM.on(mcpToggle, 'change', (e) => {
                e.stopPropagation();
                const enable = mcpToggle.checked;
                Object.keys(this.mcpServers).forEach(server => {
                    (this.mcpServers[server] || []).forEach(t => {
                        const toolId = `mcp:${server}:${t.name}`;
                        if (enable) {
                            this.disabledTools.delete(toolId);
                        } else {
                            this.disabledTools.add(toolId);
                        }
                    });
                });
                this.saveDisabledTools();
                this.renderToolsList();
            });
        }

        // Per-server toggles
        DOM.$$('.mcp-server-toggle').forEach(input => {
            DOM.on(input, 'change', (e) => {
                e.stopPropagation();
                const serverName = input.dataset.server;
                const enable = input.checked;
                const serverTools = this.mcpServers[serverName] || [];

                serverTools.forEach(t => {
                    const toolId = `mcp:${serverName}:${t.name}`;
                    if (enable) {
                        this.disabledTools.delete(toolId);
                    } else {
                        this.disabledTools.add(toolId);
                    }
                });
                this.saveDisabledTools();
                this.renderToolsList();
            });
        });

        // Individual tool toggles
        DOM.$$('.tool-toggle input[data-tool]').forEach(input => {
            DOM.on(input, 'change', (e) => {
                e.stopPropagation();
                const toolId = input.dataset.tool;
                if (input.checked) {
                    this.disabledTools.delete(toolId);
                } else {
                    this.disabledTools.add(toolId);
                }
                this.saveDisabledTools();
                this.renderToolsList();
            });
        });
    },

    /**
     * Attach section expand/collapse listeners
     */
    attachSectionExpandListeners() {
        DOM.$$('.tools-section-header-expandable').forEach(header => {
            DOM.on(header, 'click', () => {
                const groupId = header.dataset.group;
                const group = DOM.byId(groupId);
                if (group) {
                    group.classList.toggle('expanded');
                    localStorage.setItem(`${groupId}-expanded`, group.classList.contains('expanded'));
                }
            });
        });

        DOM.$$('.mcp-server-group-header').forEach(header => {
            DOM.on(header, 'click', () => {
                const group = header.closest('.mcp-server-group');
                if (group) {
                    group.classList.toggle('expanded');
                    const serverName = group.dataset.server;
                    localStorage.setItem(`mcp-server-${serverName}-expanded`, group.classList.contains('expanded'));
                }
            });
        });
    },

    /**
     * Attach tool toggle listeners
     */
    attachToolToggleListeners() {
        DOM.$$('.tool-toggle input[data-tool]').forEach(input => {
            DOM.on(input, 'change', (e) => {
                e.stopPropagation();
                const toolId = input.dataset.tool;

                if (input.checked) {
                    this.disabledTools.delete(toolId);
                } else {
                    this.disabledTools.add(toolId);
                }

                this.saveDisabledTools();
                this.updateToolItemState(input.closest('.tool-item'), !input.checked);
            });
        });
    },

    /**
     * Attach server expand listeners
     */
    attachServerExpandListeners() {
        DOM.$$('.mcp-server-group-header').forEach(header => {
            DOM.on(header, 'click', () => {
                const group = header.closest('.mcp-server-group');
                group.classList.toggle('expanded');
            });
        });
    },

    /**
     * Attach global toggle listener
     */
    attachGlobalToggleListener() {
        const globalToggle = DOM.byId('global-tools-toggle');
        if (globalToggle) {
            DOM.on(globalToggle, 'change', () => {
                if (globalToggle.checked) {
                    this.disabledTools.clear();
                } else {
                    // Disable all tools
                    this.availableTools.forEach(t => this.disabledTools.add(`builtin:${t.name}`));
                    Object.keys(this.mcpServers).forEach(server => {
                        (this.mcpServers[server] || []).forEach(t => {
                            this.disabledTools.add(`mcp:${server}:${t.name}`);
                        });
                    });
                }
                this.saveDisabledTools();
                this.renderToolsList();
            });
        }
    },

    /**
     * Attach upload button listener
     */
    attachUploadListener() {
        const uploadBtn = DOM.byId('merged-upload-btn');
        if (uploadBtn) {
            DOM.on(uploadBtn, 'click', () => {
                const imageInput = DOM.byId('image-input');
                if (imageInput) {
                    imageInput.value = '';
                    imageInput.click();
                }
                this.closePopup();
            });
        }
    },

    /**
     * Update tool item visual state
     */
    updateToolItemState(item, disabled) {
        if (item) {
            DOM.toggleClass(item, 'disabled', disabled);
        }
    },

    /**
     * Check if tool is enabled
     */
    isToolEnabled(toolId) {
        return !this.disabledTools.has(toolId);
    },

    /**
     * Get enabled tools list
     */
    getEnabledTools() {
        const enabled = [];

        this.availableTools.forEach(tool => {
            if (!this.disabledTools.has(`builtin:${tool.name}`)) {
                enabled.push(tool);
            }
        });

        return enabled;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Tools;
}
window.Tools = Tools;
