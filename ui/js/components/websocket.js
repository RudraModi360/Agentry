/**
 * AGENTRY UI - WebSocket Component
 * Handles WebSocket connection and message handling
 */

const WebSocketManager = {
    ws: null,
    reconnectDelay: 3000,
    pingInterval: null,

    /**
     * Initialize WebSocket connection
     */
    init() {
        this.connect();
        this.startPing();
        AppConfig.log('WebSocket', 'Initialized');
    },

    /**
     * Connect to WebSocket server
     */
    connect() {
        const wsUrl = `${AppConfig.getWsUrl()}/ws/chat`;

        try {
            this.ws = new WebSocket(wsUrl);
            App.state.ws = this.ws;

            this.ws.onopen = () => {
                // Send authentication token
                const token = AppConfig.getAuthToken();
                this.ws.send(JSON.stringify({ token }));
                AppConfig.log('WebSocket', 'Connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.ws.onclose = () => {
                this.updateStatus(false);
                AppConfig.log('WebSocket', 'Disconnected, reconnecting in', this.reconnectDelay + 'ms');
                setTimeout(() => this.connect(), this.reconnectDelay);
            };

            this.ws.onerror = (error) => {
                console.error('[WebSocket] Error:', error);
            };

        } catch (error) {
            console.error('[WebSocket] Connection failed:', error);
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    },

    /**
     * Update connection status UI
     */
    updateStatus(connected) {
        App.state.isConnected = connected;

        const dot = DOM.byId('status-dot');
        const text = DOM.byId('status-text');
        const sendBtn = DOM.byId('send-btn');

        if (dot) {
            DOM.removeClass(dot, 'connected', 'disconnected');
            DOM.addClass(dot, connected ? 'connected' : 'disconnected');
        }

        if (text) {
            DOM.text(text, connected ? 'Connected' : 'Disconnected');
        }

        if (sendBtn && connected) {
            sendBtn.disabled = false;
        }
    },

    /**
     * Handle WebSocket messages
     */
    handleMessage(data) {
        AppConfig.log('WebSocket', 'Message:', data.type);

        switch (data.type) {
            case 'connected':
                this.updateStatus(true);
                if (data.capabilities) {
                    window.modelCapabilities = data.capabilities;
                    this.updateCapabilities(data.capabilities);
                }
                // Reload tools now that agent/MCP is ready
                if (typeof Tools !== 'undefined') {
                    Tools.loadTools();
                }
                break;

            case 'thinking_start':
                if (!Messages.currentAssistantMessage) {
                    Messages.currentAssistantMessage = Messages.createAssistantMessage();
                    Messages.currentAssistantText = '';
                }
                Messages.removeLoadingIndicators(Messages.currentAssistantMessage);

                const contentDiv = Messages.currentAssistantMessage.querySelector('.message-content');
                Messages.thinkingContainer = DOM.create('div', { class: 'thinking-indicator' });
                Messages.thinkingContainer.dataset.startTime = Date.now();
                Messages.thinkingContainer.innerHTML = `
                    <div class="thinking-header">
                        <span class="thinking-text">
                            <span class="thinking-dots"><span></span><span></span><span></span></span>
                            Thinking
                        </span>
                        <span class="thinking-toggle">›</span>
                    </div>
                    <div class="thinking-content"></div>
                `;

                const header = Messages.thinkingContainer.querySelector('.thinking-header');
                header.addEventListener('click', (e) => {
                    e.stopPropagation();
                    Messages.thinkingContainer.classList.toggle('collapsed');
                });

                contentDiv.prepend(Messages.thinkingContainer);
                Messages.thinkingText = '';
                Messages.scrollToBottom();
                break;

            case 'thinking_delta':
                if (Messages.thinkingContainer && data.content) {
                    Messages.thinkingText += data.content;
                    const thinkingContentDiv = Messages.thinkingContainer.querySelector('.thinking-content');
                    if (thinkingContentDiv) {
                        thinkingContentDiv.textContent = Messages.thinkingText;
                    }
                    Messages.scrollToBottom();
                }
                break;

            case 'thinking_end':
                if (Messages.currentAssistantMessage) {
                    Messages.completeThinkingIndicator(Messages.thinkingContainer);
                    Messages.thinkingContainer = null;
                    Messages.thinkingText = '';
                }
                Messages.scrollToBottom();
                break;

            case 'token':
                if (!Messages.currentAssistantMessage) {
                    Messages.currentAssistantMessage = Messages.createAssistantMessage();
                    Messages.currentAssistantText = '';
                }
                if (!Messages.currentAssistantText && data.content) {
                    Messages.removeLoadingIndicators(Messages.currentAssistantMessage);
                }
                Messages.currentAssistantText += data.content;
                Messages.updateAssistantMessageText(Messages.currentAssistantMessage, Messages.currentAssistantText);
                break;

            case 'tool_start':
                if (!Messages.currentAssistantMessage) {
                    Messages.currentAssistantMessage = Messages.createAssistantMessage();
                    Messages.currentAssistantText = '';
                }
                if (Messages.currentAssistantText.trim()) {
                    Messages.updateAssistantMessageText(Messages.currentAssistantMessage, Messages.currentAssistantText);
                }
                Messages.removeLoadingIndicators(Messages.currentAssistantMessage);
                Messages.addToolCall(Messages.currentAssistantMessage, data.tool_name, data.args);
                Messages.currentAssistantText = '';
                break;

            case 'tool_end':
                if (Messages.currentAssistantMessage) {
                    Messages.updateToolCallResult(Messages.currentAssistantMessage, data.tool_name, data.result);
                    // Show spinner for continued processing
                    const contentDiv = Messages.currentAssistantMessage.querySelector('.message-content');
                    if (!contentDiv.querySelector('.spinner-container')) {
                        const spinner = DOM.create('div', { class: 'spinner-container' });
                        spinner.innerHTML = Messages.getProcessingIndicatorHTML();
                        contentDiv.appendChild(spinner);
                    }
                }
                break;

            case 'complete':
                if (data.content && data.content.trim()) {
                    if (!Messages.currentAssistantMessage) {
                        Messages.currentAssistantMessage = Messages.createAssistantMessage();
                    }
                    Messages.removeLoadingIndicators(Messages.currentAssistantMessage);
                    Messages.updateAssistantMessageText(Messages.currentAssistantMessage, data.content);
                } else if (Messages.currentAssistantMessage) {
                    Messages.removeLoadingIndicators(Messages.currentAssistantMessage);
                }

                if (Messages.currentAssistantMessage) {
                    Messages.addMessageActions(Messages.currentAssistantMessage);
                }

                // Reset state
                Messages.currentAssistantMessage = null;
                Messages.currentAssistantText = '';
                Messages.thinkingContainer = null;
                Messages.thinkingText = '';
                App.state.isProcessing = false;
                DOM.byId('send-btn').disabled = false;

                // Refresh sessions
                App.loadSessions();
                break;

            case 'session_loaded':
                Messages.renderSessionMessages(data.messages);
                break;

            case 'message_deleted':
                if (data.session_id === App.state.currentSessionId) {
                    DOM.$$('.message[style*="opacity: 0.5"]').forEach(el => el.remove());
                    App.loadSession(App.state.currentSessionId);
                }
                App.loadSessions();
                break;

            case 'session_deleted':
                if (data.session_id === App.state.currentSessionId) {
                    Messages.clear();
                    App.state.currentSessionId = null;
                }
                App.loadSessions();
                break;

            case 'session_updated':
                App.loadSessions();
                break;

            case 'tool_approval_request':
                Modals.showApproval(data.tool_name, data.args);
                break;

            case 'tool_approval_timeout':
                Modals.hideApproval();
                Messages.addErrorMessage(`Tool "${data.tool_name}" was denied due to timeout.`);
                break;

            case 'media_saved':
                if (data.media && typeof Media !== 'undefined') {
                    Media.addItem(data.media, true);
                }
                break;

            case 'error':
                if (Messages.currentAssistantMessage) {
                    Messages.removeLoadingIndicators(Messages.currentAssistantMessage);
                    Messages.currentAssistantMessage = null;
                }
                if (data.message.includes('Provider not configured')) {
                    window.location.href = '/setup.html';
                } else {
                    Messages.addErrorMessage(data.message);
                }
                App.state.isProcessing = false;
                DOM.byId('send-btn').disabled = false;
                break;

            case 'pong':
                // Keep-alive response
                break;
        }
    },

    /**
     * Update capability status
     */
    updateCapabilities(capabilities) {
        if (!capabilities) return;

        const capTools = DOM.byId('cap-tools');
        const capVision = DOM.byId('cap-vision');

        if (capTools) {
            DOM.toggleClass(capTools, 'supported', capabilities.supports_tools);
            DOM.toggleClass(capTools, 'not-supported', !capabilities.supports_tools);
        }

        if (capVision) {
            DOM.toggleClass(capVision, 'supported', capabilities.supports_vision);
            DOM.toggleClass(capVision, 'not-supported', !capabilities.supports_vision);
        }

        const attachBtn = DOM.byId('attach-image-btn');
        const messageInput = DOM.byId('message-input');

        if (attachBtn) {
            const currentAgentType = Storage.get(AppConfig.agents.storageKey, 'default');
            if (currentAgentType === 'default') {
                attachBtn.style.display = 'none';
            } else {
                attachBtn.style.display = 'flex';
            }
        }

        if (messageInput) {
            messageInput.placeholder = capabilities.supports_vision
                ? 'Type your message or attach an image...'
                : 'Type your message...';
        }
    },

    /**
     * Send message via WebSocket
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
            return true;
        }
        return false;
    },

    /**
     * Send chat message
     */
    sendMessage(content, images = []) {
        const payload = {
            type: 'message',
            content: content,
            session_id: App.state.currentSessionId
        };

        if (images && images.length > 0) {
            payload.images = images;
        }

        return this.send(payload);
    },

    /**
     * Send approval response
     */
    sendApprovalResponse(approved) {
        return this.send({
            type: 'tool_approval_response',
            approved: approved
        });
    },

    /**
     * Start ping interval
     */
    startPing() {
        this.pingInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    },

    /**
     * Stop ping interval
     */
    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    },

    /**
     * Close connection
     */
    close() {
        this.stopPing();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketManager;
}
window.WebSocketManager = WebSocketManager;
