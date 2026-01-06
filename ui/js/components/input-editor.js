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
        // We'll replace the textarea with a contenteditable div if strictly needed, 
        // OR we just assume the HTML has been updated to use a div.
        // For safety, let's try to grab the element assuming it's the right one.
        this.element = document.getElementById('message-input');

        if (!this.element) return;

        // If it's still a textarea, we might need to replace it dynamically or warn.
        // But the plan is to update HTML too. 
        // Let's assume we are working with the contenteditable div.

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
                    // If empty list item, break out of list
                    // Browser default often handles this (double enter), but for chat send:
                    // We want Enter to send, Shift+Enter to new line.
                    // BUT in a list, Enter usually creates a new item.
                    // We need to decide: does Enter ALWAYS send?
                    // User expectation in chat: Enter sends.
                    // Exception: If likely typing a list? NO, usually Shift+Enter for new line/item.
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

        // Placeholder handling (CSS should handle empty:before)
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
        // Check for "- " pattern
        // We only care if it's at the start of the block or after a newline
        // But in contenteditable, lines are often <div>s or <p>s.
        // So we check if text starts with "- "

        // Simple trigger: if user typed space, and previous chars were "- "
        if (e.inputType === 'insertText' && e.data === ' ') {
            if (text.endsWith('- ')) {
                // Check if it's the start of the line/block
                // This is tricky. simpler: regex replacing
                // If text is literally "- ", convert to list

                // Let's try detection of the specific pattern at caret
                // Actually, document.execCommand('insertUnorderedList') works on selection.

                if (text.trim() === '- ') {
                    // Delete the "- "
                    // We need to select it first?
                    // Actually, easiest valid way:
                    // 1. Remove the "- " text
                    // 2. execCommand('insertUnorderedList')

                    // Remove last 2 chars
                    const newText = text.substring(0, text.length - 2);
                    node.textContent = newText;

                    document.execCommand('insertUnorderedList');
                }
            }
        }
    },

    /**
     * Get Markdown value
     */
    getValue() {
        if (!this.element) return '';

        // Clone to not mess up UI? No, parsing structure is fine.
        // We need a custom parser from HTML to Markdown
        return this.htmlToMarkdown(this.element.innerHTML);
    },

    /**
     * Set Plain Text value
     */
    setValue(text) {
        if (!this.element) return;
        this.element.innerText = text;
        // Optional: Render it? 
        // If we want to restore history, maybe rendered. 
        // But usually setting value clears input.
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
        // Create a temporary element to parse HTML
        const temp = document.createElement('div');
        temp.innerHTML = html;

        let markdown = '';

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
                            // Block elements imply new lines usually
                            // Special case: <div><br></div> is often a newline
                            const inner = traverse(child);
                            if (result.length > 0 && !result.endsWith('\n')) result += '\n';
                            result += inner;
                            // Add newline after block unless it's the last one?
                            if (!result.endsWith('\n')) result += '\n';
                            break;

                        case 'br':
                            result += '\n';
                            break;

                        case 'ul':
                            const listContent = traverse(child);
                            if (result.length > 0 && !result.endsWith('\n')) result += '\n';
                            result += listContent;
                            if (!result.endsWith('\n')) result += '\n';
                            break;

                        case 'li':
                            // Assuming unordered list for now
                            result += '- ' + traverse(child).trim() + '\n';
                            break;

                        case 'b':
                        case 'strong':
                            result += '**' + traverse(child) + '**';
                            break;

                        case 'i':
                        case 'em':
                            result += '*' + traverse(child) + '*';
                            break;

                        default:
                            result += traverse(child);
                    }
                }
            });

            return result;
        };

        markdown = traverse(temp);
        return markdown.trim();
    },

    autoResize() {
        // For contenteditable, height auto-grows.
        // We might want to cap it via CSS (max-height)
    }
};

// Export for global use
window.InputEditor = InputEditor;
