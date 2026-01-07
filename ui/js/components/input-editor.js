/**
 * AGENTRY UI - Input Editor Component
 * Handles rich text input with Markdown-like behavior
 */

const InputEditor = {
    element: null,
    history: [],
    historyIndex: -1,

    /**
     * Initialize the editor
     */
    init() {
        this.element = document.getElementById('message-input');
        if (!this.element) return;
        this.setupEvents();
    },

    /**
     * Setup event listeners
     */
    setupEvents() {
        if (!this.element) return;

        // Handle Paste: clear formatting
        this.element.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = (e.originalEvent || e).clipboardData.getData('text/plain');
            document.execCommand('insertText', false, text);
        });

        // Handle Input triggers
        this.element.addEventListener('input', (e) => {
            this.handleInput(e);
            this.autoResize(); // If needed for outer container

            // value change check for send button
            if (window.ImageUpload && window.ImageUpload.updateSendButton) {
                window.ImageUpload.updateSendButton();
            }
        });

        // Handle Keydown
        this.element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                // Check if we are in a list
                if (document.queryCommandState('insertUnorderedList') || document.queryCommandState('insertOrderedList')) {
                    e.preventDefault();

                    // If the text is empty/whitespace, don't send
                    if (!this.getValue().trim()) return;

                    // Trigger send via Main App
                    if (window.App && window.App.sendMessage) {
                        window.App.sendMessage();
                    }
                } else {
                    e.preventDefault();
                    if (window.App && window.App.sendMessage) {
                        window.App.sendMessage();
                    }
                }
            }
        });
    },

    /**
     * Handle input for markdown triggers
     */
    handleInput(e) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return;

        const range = selection.getRangeAt(0);
        const node = range.startContainer;

        // Only trigger on text nodes
        if (node.nodeType !== Node.TEXT_NODE) return;

        const text = node.textContent;

        // Triggers for Lists and Inline Formatting
        // We check on every relevant input char or space
        if (e.inputType === 'insertText' && (e.data === ' ' || e.data === '*' || e.data === '_' || e.data === '`' || e.data === '~' || e.data === '>')) {

            // --- Block Triggers (only if space typed) ---
            if (e.data === ' ') {
                if (text.endsWith('- ') || text.endsWith('* ')) {
                    const trimmed = text.trim();
                    if (trimmed === '-' || trimmed === '*') {
                        const newText = text.substring(0, text.length - 2);
                        node.textContent = newText;
                        document.execCommand('insertUnorderedList');
                        return; // Stop processing to avoid conflicts
                    }
                }

                if (text.endsWith('1. ')) {
                    const trimmed = text.trim();
                    if (trimmed === '1.') {
                        const newText = text.substring(0, text.length - 3);
                        node.textContent = newText;
                        document.execCommand('insertOrderedList');
                        return;
                    }
                }
            }

            // --- Inline Triggers ---
            this.handleInlineMarkdown(node);
        }
    },

    /**
     * Handle inline markdown conversion
     */
    handleInlineMarkdown(node) {
        if (node.nodeType !== Node.TEXT_NODE) return;

        const text = node.textContent;
        let match;

        // Bold: **text**
        match = /\*\*([^*]+)\*\*$/.exec(text);
        if (match) {
            this.applyFormatting(node, match, 'bold');
            return;
        }

        // Italic: *text* (avoiding * at start of line which is list)
        // We ensure it's not the start of the string or preceded by space/char if needed, 
        // strictly matching *text*
        match = /(?<!^)(?<!\*)\*([^*]+)\*$/.exec(text);
        if (match) {
            this.applyFormatting(node, match, 'italic');
            return;
        }

        // Code: `text`
        match = /`([^`]+)`$/.exec(text);
        if (match) {
            this.applyFormatting(node, match, 'code');
            return;
        }

        // Strike: ~~text~~
        match = /~~([^~]+)~~$/.exec(text);
        if (match) {
            this.applyFormatting(node, match, 'strikethrough');
            return;
        }
    },

    /**
     * Apply formatting command
     */
    applyFormatting(node, match, command) {
        const fullMatch = match[0];
        const content = match[1];
        const startOffset = node.textContent.length - fullMatch.length;
        const endOffset = node.textContent.length;

        const range = document.createRange();
        range.setStart(node, startOffset);
        range.setEnd(node, endOffset);

        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        let htmlNode = '';
        if (command === 'bold') htmlNode = `<b>${content}</b>`;
        else if (command === 'italic') htmlNode = `<i>${content}</i>`;
        else if (command === 'strikethrough') htmlNode = `<s>${content}</s>`;
        else if (command === 'code') htmlNode = `<code>${content}</code>`;

        // Insert and add space to escape the format
        document.execCommand('insertHTML', false, htmlNode + '&nbsp;');
    },

    /**
     * Get Markdown value
     */
    getValue() {
        if (!this.element) return '';
        return this.htmlToMarkdown(this.element.innerHTML);
    },

    /**
     * Set Plain Text value
     */
    setValue(text) {
        if (!this.element) return;
        this.element.innerText = text;
    },

    /**
     * Clear input
     */
    clear() {
        if (!this.element) return;
        this.element.innerHTML = '';
    },

    /**
     * Convert HTML to Markdown (Simplified for Chat)
     */
    htmlToMarkdown(html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;

        // Recursive function to traverse nodes
        const traverse = (node) => {
            let result = '';

            node.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE) {
                    result += child.textContent;
                } else if (child.nodeType === Node.ELEMENT_NODE) {
                    const tag = child.tagName.toLowerCase();

                    switch (tag) {
                        case 'div':
                        case 'p':
                            const inner = traverse(child);
                            if (result.length > 0 && !result.endsWith('\n')) result += '\n';
                            result += inner;
                            if (!result.endsWith('\n') && child.nextSibling) result += '\n';
                            break;

                        case 'br':
                            result += '\n';
                            break;

                        case 'ul':
                        case 'ol':
                            const listContent = traverse(child);
                            if (result.length > 0 && !result.endsWith('\n')) result += '\n';
                            result += listContent;
                            if (!result.endsWith('\n')) result += '\n';
                            break;

                        case 'li':
                            // Check parent for ol/ul
                            const parentTag = child.parentElement ? child.parentElement.tagName.toLowerCase() : 'ul';
                            const prefix = parentTag === 'ol' ? '1. ' : '- ';
                            result += prefix + traverse(child).trim() + '\n';
                            break;

                        case 'b':
                        case 'strong':
                            result += '**' + traverse(child) + '**';
                            break;

                        case 'i':
                        case 'em':
                            result += '*' + traverse(child) + '*';
                            break;

                        case 'code':
                            result += '`' + traverse(child) + '`';
                            break;

                        case 's':
                        case 'strike':
                        case 'del':
                            result += '~~' + traverse(child) + '~~';
                            break;

                        default:
                            result += traverse(child);
                    }
                }
            });

            return result;
        };

        return traverse(temp).trim();
    },

    autoResize() {
        // contenteditable handles auto-height natively
    }
};

// Export for global use
window.InputEditor = InputEditor;
