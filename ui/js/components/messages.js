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
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="message-action-btn delete-btn" title="Delete message">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
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
     * Update assistant message text
     */
    updateAssistantMessageText(msgElement, content) {
        if (content && content.length > 0) {
            this.removeLoadingIndicators(msgElement);
        }

        if (!content || !content.trim()) return;

        const contentDiv = msgElement.querySelector('.message-content');
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
     */
    addToolCall(msgElement, toolName, args) {
        const contentDiv = msgElement.querySelector('.message-content');

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
     */
    updateToolCallResult(msgElement, toolName, result) {
        const contentDiv = msgElement.querySelector('.message-content');
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
        this.container.innerHTML = '';

        if (!messages || messages.length === 0) {
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
        if (textEl) textEl.textContent = 'Thought for ' + durationText;

        const toggle = indicator.querySelector('.thinking-toggle');
        if (toggle) toggle.textContent = '▶';
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
