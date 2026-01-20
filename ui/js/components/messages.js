/**
 * AGENTRY UI - Messages Component
 * Handles all message rendering, formatting, and interactions
 */

const Messages = {
    // State
    currentAssistantMessage: null,
    currentAssistantText: '',
    thinkingContainer: null,
    thinkingText: '',
    selectedImagesData: [],

    // Streaming optimization state
    _streamBuffer: '',
    _streamRenderTimer: null,
    _streamRenderDelay: 50, // ms between renders
    _lastRenderTime: 0,
    _pendingMediaResults: [], // Buffer for media_search results

    // Elements
    container: null,
    emptyState: null,

    /**
     * Initialize messages component
     */
    init() {
        this.container = DOM.byId('messages-container');
        this.emptyState = DOM.byId('empty-state');

        // Setup global click handlers
        DOM.on(document, 'click', (e) => {
            if (!e.target.closest('.tool-call')) {
                DOM.$$('.tool-call:not(.collapsed)').forEach(tc => {
                    tc.classList.add('collapsed');
                    const toggle = tc.querySelector('.tool-call-toggle');
                    if (toggle) toggle.textContent = '▶';
                });
            }
        });

        AppConfig.log('Messages', 'Initialized');
    },

    /**
     * Clear all messages
     */
    clear() {
        if (!this.container) return;
        this.container.innerHTML = '';
        if (this.emptyState) {
            this.emptyState.style.display = 'flex';
            this.container.appendChild(this.emptyState);
        }
    },

    /**
     * Hide empty state
     */
    hideEmptyState() {
        if (this.emptyState) {
            this.emptyState.style.display = 'none';
        }
    },

    /**
     * Add user message
     */
    addUserMessage(content, messageIndex = null, imageData = null, extraImages = []) {
        this.hideEmptyState();

        const msg = DOM.create('div', { class: 'message user' });
        msg.dataset.originalContent = typeof content === 'string' ? content : JSON.stringify(content);
        if (messageIndex !== null) {
            msg.dataset.messageIndex = messageIndex;
        }

        // Parse content if multimodal
        let displayContent = content;
        let imagesFromContent = [];

        if (typeof content === 'object' && content !== null) {
            if (Array.isArray(content)) {
                let textParts = [];
                content.forEach(part => {
                    if (part.type === 'text') {
                        textParts.push(part.text || '');
                    } else if (part.type === 'image' && part.data) {
                        let src = part.data;
                        if (!src.startsWith('data:') && !src.startsWith('http')) {
                            src = 'data:image/png;base64,' + src;
                        }
                        imagesFromContent.push(src);
                    } else if (part.type === 'image_url' && part.image_url?.url) {
                        imagesFromContent.push(part.image_url.url);
                    }
                });
                displayContent = textParts.join('\n');
            } else if (content.text) {
                displayContent = content.text;
            }
        }

        // Combine all images
        let allImages = [...imagesFromContent];
        if (imageData) allImages.push(imageData);
        if (extraImages && Array.isArray(extraImages)) allImages.push(...extraImages);

        let imagesHtml = '';
        if (allImages.length > 0) {
            imagesHtml = `<div class="message-images-grid" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                ${allImages.map(img => `<div class="message-image-item" style="width: 80px; height: 80px; border-radius: 8px; overflow: hidden; border: 1px solid var(--card-border);"><img src="${img}" style="width: 100%; height: 100%; object-fit: cover; cursor: pointer;" onclick="window.open(this.src)" title="Click to view full image"></div>`).join('')}
            </div>`;
        }

        msg.innerHTML = `
            <div class="message-content">
                <div class="message-text">${this.formatMessage(displayContent)}</div>
                ${imagesHtml}
                <div class="message-actions">
                    <button class="message-action-btn edit-btn" title="Edit message">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="message-action-btn delete-btn" title="Delete message">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        // Add event handlers
        const editBtn = msg.querySelector('.edit-btn');
        DOM.on(editBtn, 'click', (e) => {
            e.stopPropagation();
            this.startEditMessage(msg);
        });

        const deleteBtn = msg.querySelector('.delete-btn');
        DOM.on(deleteBtn, 'click', (e) => {
            e.stopPropagation();
            this.deleteMessage(msg);
        });

        this.container.appendChild(msg);
        this.scrollToBottom();

        return msg;
    },

    /**
     * Create assistant message placeholder
     */
    createAssistantMessage(messageIndex = null) {
        this.hideEmptyState();

        const msg = DOM.create('div', { class: 'message assistant' });
        if (messageIndex !== null) {
            msg.dataset.messageIndex = messageIndex;
        }

        msg.innerHTML = `
            <div class="message-content">
                <div class="spinner-container">
                    ${this.getProcessingIndicatorHTML()}
                </div>
                <div class="message-text" style="display:none;"></div>
            </div>
        `;

        this.container.appendChild(msg);
        this.scrollToBottom();

        return msg;
    },

    /**
     * Update assistant message text with streaming optimization
     * Uses debounced rendering to prevent UI freezes during fast token streaming
     */
    updateAssistantMessageText(msgElement, content, forceRender = false) {
        if (content && content.length > 0) {
            this.removeLoadingIndicators(msgElement);
        }

        if (!content || !content.trim()) return;

        // Store the content
        this._streamBuffer = content;

        const now = Date.now();
        const timeSinceLastRender = now - this._lastRenderTime;

        // Clear any pending render
        if (this._streamRenderTimer) {
            clearTimeout(this._streamRenderTimer);
            this._streamRenderTimer = null;
        }

        // If enough time has passed or forceRender, render immediately
        if (forceRender || timeSinceLastRender >= this._streamRenderDelay) {
            this._renderStreamContent(msgElement, content);
            this._lastRenderTime = now;
        } else {
            // Schedule a render for later
            this._streamRenderTimer = setTimeout(() => {
                this._renderStreamContent(msgElement, this._streamBuffer);
                this._lastRenderTime = Date.now();
                this._streamRenderTimer = null;
            }, this._streamRenderDelay - timeSinceLastRender);
        }
    },

    /**
     * Internal method to actually render the streamed content
     */
    _renderStreamContent(msgElement, content) {
        if (!msgElement || !content) return;

        const contentDiv = msgElement.querySelector('.message-content');
        if (!contentDiv) return;

        const toolsContainer = contentDiv.querySelector('.tool-calls-container');

        if (toolsContainer) {
            let afterTextDiv = toolsContainer.nextElementSibling;
            if (!afterTextDiv || !afterTextDiv.classList.contains('message-text-after')) {
                afterTextDiv = DOM.create('div', { class: 'message-text message-text-after' });
                toolsContainer.parentNode.insertBefore(afterTextDiv, toolsContainer.nextSibling);
            }
            afterTextDiv.innerHTML = this.formatMessage(content);
            afterTextDiv.style.display = 'block';
        } else {
            let textDiv = contentDiv.querySelector('.message-text');
            if (!textDiv) {
                textDiv = DOM.create('div', { class: 'message-text' });
                contentDiv.appendChild(textDiv);
            }
            textDiv.innerHTML = this.formatMessage(content);
            textDiv.style.display = 'block';
        }

        this.scrollToBottom();
    },

    /**
     * Force render any pending stream content (call on message complete)
     */
    flushStreamBuffer(msgElement) {
        if (this._streamRenderTimer) {
            clearTimeout(this._streamRenderTimer);
            this._streamRenderTimer = null;
        }
        if (this._streamBuffer && msgElement) {
            this._renderStreamContent(msgElement, this._streamBuffer);
        }
        this._streamBuffer = '';
        this._lastRenderTime = 0;
    },

    /**
     * Add message actions (copy, delete buttons)
     */
    addMessageActions(msgElement) {
        const contentDiv = msgElement.querySelector('.message-content');
        if (contentDiv.querySelector('.message-actions')) return;

        const actionsDiv = DOM.create('div', { class: 'message-actions' });
        actionsDiv.innerHTML = `
            <button class="message-action-btn copy-btn" title="Copy response">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
            </button>
            <button class="message-action-btn delete-btn" title="Delete message">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        `;

        contentDiv.appendChild(actionsDiv);

        const deleteBtn = actionsDiv.querySelector('.delete-btn');
        DOM.on(deleteBtn, 'click', (e) => {
            e.stopPropagation();
            this.deleteMessage(msgElement);
        });

        const copyBtn = actionsDiv.querySelector('.copy-btn');
        DOM.on(copyBtn, 'click', (e) => {
            e.stopPropagation();
            const textDivs = msgElement.querySelectorAll('.message-text, .message-text-after');
            let text = '';
            textDivs.forEach(div => { text += div.innerText + '\n'; });
            this.copyToClipboard(text.trim(), copyBtn);
        });
    },

    /**
     * Add tool call to message
     * Special handling for media_search - renders inline carousel instead of collapsible
     */
    addToolCall(msgElement, toolName, args) {
        const contentDiv = msgElement.querySelector('.message-content');

        // Special handling for media_search - create a minimal inline indicator
        if (toolName === 'media_search' || toolName === 'image_search') {
            // Create or get media container
            let mediaCarousel = contentDiv.querySelector('.inline-media-carousel');
            if (!mediaCarousel) {
                mediaCarousel = DOM.create('div', { class: 'inline-media-carousel' });
                mediaCarousel.innerHTML = `
                    <div class="media-carousel-header">
                        <span class="media-carousel-icon">🔍</span>
                        <span class="media-carousel-text">Searching for media...</span>
                    </div>
                    <div class="media-carousel-items"></div>
                `;
                const textDiv = contentDiv.querySelector('.message-text');
                if (textDiv) {
                    contentDiv.insertBefore(mediaCarousel, textDiv.nextSibling);
                } else {
                    contentDiv.appendChild(mediaCarousel);
                }
            }
            this.scrollToBottom();
            return;
        }

        let toolsContainer = contentDiv.querySelector('.tool-calls-container');
        if (!toolsContainer) {
            toolsContainer = DOM.create('div', { class: 'tool-calls-container' });
            const spinnerContainer = contentDiv.querySelector('.spinner-container');
            const textDiv = contentDiv.querySelector('.message-text');
            if (spinnerContainer) {
                spinnerContainer.parentNode.insertBefore(toolsContainer, spinnerContainer.nextSibling);
            } else if (textDiv) {
                contentDiv.insertBefore(toolsContainer, textDiv);
            } else {
                contentDiv.appendChild(toolsContainer);
            }
        }

        const toolDiv = DOM.create('div', { class: 'tool-call collapsed' });
        toolDiv.dataset.toolName = toolName;

        let argsHtml = '';
        if (args && typeof args === 'object' && Object.keys(args).length > 0) {
            argsHtml = `
                <div class="tool-call-section">
                    <div class="tool-call-section-title">Tool Params</div>
                    <div class="tool-call-args">${DOM.escapeHtml(JSON.stringify(args, null, 2))}</div>
                </div>
            `;
        }

        toolDiv.innerHTML = `
            <div class="tool-call-header">
                <span class="tool-call-name">${DOM.escapeHtml(toolName)}</span>
                <span class="tool-spinner">
                    <span class="tool-spinner-leaf"></span>
                    <span class="tool-spinner-leaf"></span>
                    <span class="tool-spinner-leaf"></span>
                    <span class="tool-spinner-leaf"></span>
                </span>
                <span class="tool-call-toggle">▶</span>
            </div>
            <div class="tool-call-body">${argsHtml}</div>
        `;

        const header = toolDiv.querySelector('.tool-call-header');
        DOM.on(header, 'click', (e) => {
            e.stopPropagation();
            DOM.$$('.tool-call:not(.collapsed)').forEach(tc => {
                if (tc !== toolDiv) {
                    tc.classList.add('collapsed');
                    const toggle = tc.querySelector('.tool-call-toggle');
                    if (toggle) toggle.textContent = '▶';
                }
            });
            toolDiv.classList.toggle('collapsed');
            toolDiv.querySelector('.tool-call-toggle').textContent =
                toolDiv.classList.contains('collapsed') ? '▶' : '▼';
        });

        toolsContainer.appendChild(toolDiv);
        this.scrollToBottom();
    },

    /**
     * Update tool call with result
     * Special handling for media_search - renders inline carousel
     */
    updateToolCallResult(msgElement, toolName, result) {
        const contentDiv = msgElement.querySelector('.message-content');

        // Special handling for media_search - render inline carousel
        if (toolName === 'media_search' || toolName === 'image_search') {
            this._renderMediaCarouselResult(contentDiv, result);
            this.scrollToBottom();
            return;
        }

        const toolDivs = contentDiv.querySelectorAll('.tool-call');

        let targetToolDiv = null;
        toolDivs.forEach(div => {
            if (div.dataset.toolName === toolName && !div.classList.contains('completed')) {
                targetToolDiv = div;
            }
        });

        if (targetToolDiv) {
            let isSuccess = true;
            if (result && typeof result === 'object' && (result.success === false || result.error)) {
                isSuccess = false;
            } else if (typeof result === 'string' &&
                (result.toLowerCase().includes('error') || result.includes('STDERR'))) {
                isSuccess = false;
            }

            targetToolDiv.classList.add('completed');
            if (!isSuccess) targetToolDiv.classList.add('failed');

            if (result) {
                let bodyDiv = targetToolDiv.querySelector('.tool-call-body');
                if (!bodyDiv) {
                    bodyDiv = DOM.create('div', { class: 'tool-call-body' });
                    targetToolDiv.appendChild(bodyDiv);
                }

                if (!bodyDiv.querySelector('.tool-call-result')) {
                    const sectionDiv = DOM.create('div', { class: 'tool-call-section' });
                    sectionDiv.innerHTML = `
                        <div class="tool-call-section-title">Tool Result</div>
                        <div class="tool-call-result"></div>
                    `;
                    const resultText = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
                    sectionDiv.querySelector('.tool-call-result').textContent =
                        resultText.substring(0, 1000) + (resultText.length > 1000 ? '\n... (truncated)' : '');
                    bodyDiv.appendChild(sectionDiv);
                }
            }

            targetToolDiv.classList.add('collapsed');
            this.scrollToBottom();
        }
    },

    /**
     * Render media search results in a horizontal carousel
     */
    _renderMediaCarouselResult(contentDiv, result) {
        const carousel = contentDiv.querySelector('.inline-media-carousel');
        if (!carousel) return;

        // Parse result
        let mediaItems = [];
        try {
            if (typeof result === 'string') {
                // Try to parse JSON from result
                const jsonMatch = result.match(/\[[\s\S]*\]/);
                if (jsonMatch) {
                    mediaItems = JSON.parse(jsonMatch[0]);
                }
            } else if (Array.isArray(result)) {
                mediaItems = result;
            } else if (result && result.results) {
                mediaItems = result.results;
            } else if (result && result.images) {
                mediaItems = result.images;
            }
        } catch (e) {
            console.warn('Failed to parse media results:', e);
        }

        // Update header
        const header = carousel.querySelector('.media-carousel-header');
        if (header) {
            if (mediaItems.length > 0) {
                header.innerHTML = `
                    <span class="media-carousel-icon">🖼️</span>
                    <span class="media-carousel-text">Found ${mediaItems.length} ${mediaItems.length === 1 ? 'image' : 'images'}</span>
                `;
            } else {
                header.innerHTML = `
                    <span class="media-carousel-icon">📷</span>
                    <span class="media-carousel-text">No images found</span>
                `;
            }
        }

        // Render items in carousel
        const itemsContainer = carousel.querySelector('.media-carousel-items');
        if (itemsContainer && mediaItems.length > 0) {
            itemsContainer.innerHTML = mediaItems.slice(0, 10).map(item => {
                const url = item.url || item.image_url || item.thumbnail || item.src || '';
                const title = item.title || item.alt || item.description || '';
                const source = item.source || item.domain || '';
                const link = item.link || item.page_url || url;

                if (!url) return '';

                return `
                    <div class="media-carousel-item" onclick="window.open('${DOM.escapeHtml(link)}', '_blank')">
                        <img src="${DOM.escapeHtml(url)}" alt="${DOM.escapeHtml(title)}" 
                             onerror="this.parentElement.style.display='none'" 
                             loading="lazy" />
                        <div class="media-carousel-item-info">
                            <span class="media-item-title">${DOM.escapeHtml(title.substring(0, 40) || 'Image')}</span>
                            ${source ? `<span class="media-item-source">${DOM.escapeHtml(source)}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }

        carousel.classList.add('loaded');
    },

    /**
     * Add error message
     */
    addErrorMessage(message) {
        const msg = DOM.create('div', { class: 'message assistant' });
        msg.innerHTML = `
            <div class="message-content">
                <div class="message-text" style="color: var(--error);">⚠️ ${DOM.escapeHtml(message)}</div>
            </div>
        `;
        this.container.appendChild(msg);
        this.scrollToBottom();
    },

    /**
     * Render session messages
     */
    renderSessionMessages(messages) {
        AppConfig.log('Messages', 'Rendering', messages ? messages.length : 0, 'messages');
        this.container.innerHTML = '';

        if (!messages || messages.length === 0) {
            console.log('[Messages] No messages to render, showing empty state');
            if (this.emptyState) {
                this.container.appendChild(this.emptyState);
                this.emptyState.style.display = 'flex';
            }
            return;
        }

        this.hideEmptyState();

        let currentAssistantEl = null;
        let lastRole = null;

        messages.forEach((msg, idx) => {
            if (msg.role === 'user') {
                if (currentAssistantEl) {
                    this.addMessageActions(currentAssistantEl);
                }
                this.addUserMessage(msg.content, idx);
                currentAssistantEl = null;
                lastRole = 'user';
            } else if (msg.role === 'assistant') {
                if (!currentAssistantEl || lastRole === 'user') {
                    currentAssistantEl = this.createAssistantMessage(idx);
                    this.removeLoadingIndicators(currentAssistantEl);
                }

                const content = typeof msg.content === 'string' ? msg.content : (msg.content || '');
                if (content) {
                    this.updateAssistantMessageText(currentAssistantEl, content);
                }

                if (msg.tool_calls && Array.isArray(msg.tool_calls)) {
                    msg.tool_calls.forEach(tc => {
                        const toolName = tc.function?.name || tc.name || 'unknown';
                        const toolArgs = tc.function?.arguments || tc.arguments || {};
                        const parsedArgs = typeof toolArgs === 'string' ? JSON.parse(toolArgs) : toolArgs;
                        this.addToolCall(currentAssistantEl, toolName, parsedArgs);
                    });
                }

                this.removeLoadingIndicators(currentAssistantEl);
                lastRole = 'assistant';
            } else if (msg.role === 'tool' && currentAssistantEl) {
                const toolName = msg.name || msg.tool_call_id || 'tool';
                this.updateToolCallResult(currentAssistantEl, toolName, msg.content);
                this.removeLoadingIndicators(currentAssistantEl);
                lastRole = 'tool';
            }
        });

        if (currentAssistantEl) {
            this.addMessageActions(currentAssistantEl);
        }

        this.scrollToBottom();
    },

    /**
     * Get processing indicator HTML
     */
    getProcessingIndicatorHTML() {
        return `
            <div class="processing-indicator" data-start-time="${Date.now()}">
                <span class="processing-text">
                    Processing
                    <span class="processing-dots">
                        <span class="processing-dot"></span>
                        <span class="processing-dot"></span>
                        <span class="processing-dot"></span>
                    </span>
                </span>
            </div>
        `;
    },

    /**
     * Remove loading indicators
     */
    removeLoadingIndicators(msgElement) {
        if (!msgElement) return;

        const processingIndicator = msgElement.querySelector('.processing-indicator');
        if (processingIndicator) processingIndicator.remove();

        const thinkingIndicator = msgElement.querySelector('.thinking-indicator:not(.completed)');
        if (thinkingIndicator) {
            this.completeThinkingIndicator(thinkingIndicator);
        }

        const spinnerContainers = msgElement.querySelectorAll('.spinner-container');
        spinnerContainers.forEach(container => {
            if (!container.querySelector('.thinking-indicator')) {
                container.remove();
            }
        });
    },

    /**
     * Complete thinking indicator
     */
    completeThinkingIndicator(indicator) {
        const startTime = parseInt(indicator.dataset.startTime || Date.now());
        const duration = Math.round((Date.now() - startTime) / 1000);
        const durationText = duration <= 0 ? '< 1s' :
            (duration < 60 ? `${duration}s` : `${Math.floor(duration / 60)}m ${duration % 60}s`);

        indicator.classList.add('completed', 'collapsed');

        const textEl = indicator.querySelector('.thinking-text');
        if (textEl) {
            textEl.innerHTML = `Thought for <span class="thinking-time">${durationText}</span>`;
        }
    },

    /**
     * Start editing a message
     */
    startEditMessage(msgElement) {
        if (App.state.isProcessing) return;

        let contentToEdit = msgElement.dataset.originalContent;

        try {
            if (contentToEdit && contentToEdit.trim().startsWith('[')) {
                const parsed = JSON.parse(contentToEdit);
                if (Array.isArray(parsed)) {
                    contentToEdit = parsed.filter(p => p.type === 'text').map(p => p.text).join('\n');
                }
            }
        } catch (e) { }

        const contentDiv = msgElement.querySelector('.message-content');
        const textDiv = contentDiv.querySelector('.message-text');
        const actionsDiv = contentDiv.querySelector('.message-actions');

        actionsDiv.style.display = 'none';
        textDiv.style.display = 'none';

        const editContainer = DOM.create('div', { class: 'message-edit-container' });
        editContainer.innerHTML = `
            <textarea class="message-edit-input">${DOM.escapeHtml(contentToEdit)}</textarea>
            <div class="message-edit-actions">
                <button class="btn-sm save">Save & Regenerate</button>
                <button class="btn-sm cancel">Cancel</button>
            </div>
        `;

        contentDiv.appendChild(editContainer);

        const textarea = editContainer.querySelector('textarea');
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);

        editContainer.querySelector('.cancel').addEventListener('click', () => {
            editContainer.remove();
            actionsDiv.style.display = '';
            textDiv.style.display = '';
        });

        editContainer.querySelector('.save').addEventListener('click', async () => {
            const newContent = textarea.value.trim();
            if (!newContent) return;
            await this.editAndRegenerate(msgElement, newContent);
        });
    },

    /**
     * Edit message and regenerate response
     */
    async editAndRegenerate(msgElement, newContent) {
        let sibling = msgElement.nextElementSibling;
        while (sibling) {
            const next = sibling.nextElementSibling;
            if (sibling !== this.emptyState) sibling.remove();
            sibling = next;
        }

        msgElement.dataset.originalContent = newContent;
        const textDiv = msgElement.querySelector('.message-text');
        textDiv.innerHTML = DOM.escapeHtml(newContent);
        textDiv.style.display = '';

        const editContainer = msgElement.querySelector('.message-edit-container');
        if (editContainer) editContainer.remove();

        const actionsDiv = msgElement.querySelector('.message-actions');
        if (actionsDiv) actionsDiv.style.display = '';

        if (App.state.ws && App.state.ws.readyState === WebSocket.OPEN && App.state.currentSessionId) {
            App.state.isProcessing = true;
            DOM.byId('send-btn').disabled = true;

            const allMessages = Array.from(this.container.querySelectorAll('.message'));
            const msgIndex = allMessages.indexOf(msgElement);
            const backendIndex = msgIndex + 1;

            this.currentAssistantMessage = this.createAssistantMessage();
            this.currentAssistantText = '';

            App.state.ws.send(JSON.stringify({
                type: 'message',
                content: newContent,
                session_id: App.state.currentSessionId,
                is_edit: true,
                edit_index: backendIndex
            }));
        }
    },

    /**
     * Delete message
     */
    async deleteMessage(msgElement) {
        const isUserMessage = msgElement.classList.contains('user');
        const confirmMessage = isUserMessage
            ? 'Delete this message and its response? This cannot be undone.'
            : 'Delete this response? The original question will remain.';

        if (!confirm(confirmMessage)) return;

        let backendIndex;
        if (msgElement.dataset.messageIndex) {
            backendIndex = parseInt(msgElement.dataset.messageIndex, 10);
        } else {
            const allMessages = Array.from(this.container.querySelectorAll('.message'));
            const domIndex = allMessages.indexOf(msgElement);
            if (domIndex === -1) return;
            backendIndex = domIndex + 1;
        }

        if (App.state.ws && App.state.ws.readyState === WebSocket.OPEN && App.state.currentSessionId) {
            msgElement.style.opacity = '0.5';
            msgElement.style.pointerEvents = 'none';

            if (isUserMessage) {
                let sibling = msgElement.nextElementSibling;
                while (sibling && !sibling.classList.contains('user') && sibling !== this.emptyState) {
                    sibling.style.opacity = '0.5';
                    sibling.style.pointerEvents = 'none';
                    sibling = sibling.nextElementSibling;
                }
            }

            App.state.ws.send(JSON.stringify({
                type: 'delete_message',
                session_id: App.state.currentSessionId,
                index: backendIndex
            }));
        }
    },

    /**
     * Format message content with markdown
     */
    formatMessage(content) {
        if (!content) return '';

        if (Array.isArray(content)) {
            return content.map(part => {
                if (part.type === 'text') return this.formatMessage(part.text);
                if (part.type === 'image') {
                    let src = part.data || part.url;
                    if (src && !src.startsWith('data:') && !src.startsWith('http') && !src.startsWith('/')) {
                        src = `data:image/png;base64,${src}`;
                    }
                    return `<div class="message-image"><img src="${src}" onclick="window.open(this.src)" /></div>`;
                }
                return '';
            }).join('');
        }

        if (typeof content !== 'string') return '';

        try {
            // Pre-process: Convert YouTube markers to rich embeds
            content = this.processYouTubeEmbeds(content);

            // Pre-process: Enhance inline images with better styling
            content = this.processInlineImages(content);

            const renderer = new marked.Renderer();

            renderer.code = (codeOrToken, language) => {
                let code, lang;
                if (typeof codeOrToken === 'object' && codeOrToken !== null) {
                    code = codeOrToken.text || codeOrToken.raw || '';
                    lang = codeOrToken.lang || 'plaintext';
                } else {
                    code = codeOrToken || '';
                    lang = language || 'plaintext';
                }

                let highlightedCode;
                try {
                    const validLang = hljs.getLanguage(lang) ? lang : 'plaintext';
                    highlightedCode = hljs.highlight(code, { language: validLang }).value;
                } catch (e) {
                    highlightedCode = DOM.escapeHtml(code);
                }

                const blockId = 'code-' + Math.random().toString(36).substr(2, 9);
                return `
                    <div class="code-block-container" data-block-id="${blockId}">
                        <div class="code-block-header">
                            <span class="code-block-language">${lang}</span>
                            <button class="copy-block-btn" onclick="Messages.copyCodeBlock(this)" title="Copy">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="9" y="9" width="13" height="13" rx="2"/>
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                                </svg>
                                <span>Copy</span>
                            </button>
                        </div>
                        <pre><code class="hljs" data-code="${btoa(unescape(encodeURIComponent(code)))}">${highlightedCode}</code></pre>
                    </div>
                `;
            };

            marked.setOptions({ renderer, gfm: true, breaks: true });
            return marked.parse(content);
        } catch (e) {
            console.error('Markdown parsing error:', e);
            return content;
        }
    },

    /**
     * Process YouTube embed markers and convert to rich cards
     */
    processYouTubeEmbeds(content) {
        // Match <!-- YOUTUBE:VIDEO_ID --> followed by markdown image link
        const youtubePattern = /<!-- YOUTUBE:([a-zA-Z0-9_-]{11}) -->\s*\n?\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)\s*\n?\*([^*]+)\*/g;

        return content.replace(youtubePattern, (match, videoId, title, thumbnail, url, channel) => {
            // Clean up the title (remove emoji if present)
            const cleanTitle = title.replace(/🎬\s*/, '').trim();
            const cleanChannel = channel.replace(/📺\s*/, '').trim();

            return `
<div class="youtube-embed-card" onclick="window.open('${url}', '_blank')">
    <div class="youtube-thumbnail">
        <img src="${thumbnail}" alt="${cleanTitle}" onerror="this.src='https://img.youtube.com/vi/${videoId}/hqdefault.jpg'" />
        <div class="youtube-play-btn">
            <svg viewBox="0 0 68 48" width="68" height="48">
                <path class="youtube-play-bg" d="M66.52,7.74c-0.78-2.93-2.49-5.41-5.42-6.19C55.79,.13,34,0,34,0S12.21,.13,6.9,1.55 C3.97,2.33,2.27,4.81,1.48,7.74C0.06,13.05,0,24,0,24s0.06,10.95,1.48,16.26c0.78,2.93,2.49,5.41,5.42,6.19 C12.21,47.87,34,48,34,48s21.79-0.13,27.1-1.55c2.93-0.78,4.64-3.26,5.42-6.19C67.94,34.95,68,24,68,24S67.94,13.05,66.52,7.74z" fill="#f00"/>
                <path d="M 45,24 27,14 27,34" fill="#fff"/>
            </svg>
        </div>
    </div>
    <div class="youtube-info">
        <div class="youtube-title">${cleanTitle}</div>
        <div class="youtube-channel">${cleanChannel}</div>
    </div>
</div>
`;
        });
    },

    /**
     * Process inline images to add better styling and containers
     */
    processInlineImages(content) {
        // Match markdown images: ![alt](url)
        // Followed by optional source line: *Source: [text](url)*
        const imageWithSourcePattern = /!\[([^\]]*)\]\(([^)]+)\)\s*\n?\*Source:\s*\[([^\]]*)\]\(([^)]+)\)\*/g;

        content = content.replace(imageWithSourcePattern, (match, alt, imageUrl, sourceName, sourceUrl) => {
            return `
<div class="inline-media-card">
    <div class="inline-media-image">
        <img src="${imageUrl}" alt="${alt}" onclick="window.open('${imageUrl}', '_blank')" 
             onerror="this.parentElement.style.display='none'" />
    </div>
    <div class="inline-media-source">
        <a href="${sourceUrl}" target="_blank" rel="noopener">${sourceName || 'Source'}</a>
    </div>
</div>
`;
        });

        // Handle standalone markdown images without source
        const standaloneImagePattern = /!\[([^\]]*)\]\((https?:\/\/[^)]+)\)(?!\s*\n?\*Source)/g;

        content = content.replace(standaloneImagePattern, (match, alt, imageUrl) => {
            // Skip YouTube thumbnails (they're handled by processYouTubeEmbeds)
            if (imageUrl.includes('youtube.com') || imageUrl.includes('ytimg.com')) {
                return match;
            }

            return `
<div class="inline-media-image standalone">
    <img src="${imageUrl}" alt="${alt}" onclick="window.open('${imageUrl}', '_blank')"
         onerror="this.parentElement.style.display='none'" />
</div>
`;
        });

        return content;
    },

    /**
     * Copy code block
     */
    async copyCodeBlock(btn) {
        try {
            const container = btn.closest('.code-block-container');
            const codeEl = container.querySelector('code');
            const code = decodeURIComponent(escape(atob(codeEl.dataset.code)));

            await navigator.clipboard.writeText(code);

            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg><span>Copied!</span>';
            btn.classList.add('copied');

            setTimeout(() => {
                btn.innerHTML = originalHtml;
                btn.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    },

    /**
     * Copy to clipboard with feedback
     */
    async copyToClipboard(text, btn) {
        try {
            await navigator.clipboard.writeText(text);
            if (btn) {
                btn.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
                setTimeout(() => {
                    btn.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
                }, 2000);
            }
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    },

    /**
     * Scroll to bottom
     */
    scrollToBottom(force = false) {
        if (!this.container) return;
        if (force || App.state.isAutoScrollEnabled) {
            this.container.scrollTop = this.container.scrollHeight;
            if (force) {
                App.state.isAutoScrollEnabled = true;
                const scrollBtn = DOM.byId('scroll-bottom-btn');
                if (scrollBtn) scrollBtn.classList.remove('visible');
            }
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Messages;
}
window.Messages = Messages;
