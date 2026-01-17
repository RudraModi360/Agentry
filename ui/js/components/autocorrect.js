/**
 * AGENTRY UI - AutoCorrect Component
 * Handles real-time spelling and grammar correction in the chat input
 */

const AutoCorrect = {
    isCorrecting: false,

    /**
     * Initialize the component
     */
    init() {
        // Autocorrect button disabled - not needed
        // this.injectButton();
        // this.setupEventListeners();
        AppConfig.log('AutoCorrect', 'Disabled');
    },

    /**
     * Inject the auto-correct button into the input area
     */
    injectButton() {
        const inputWrapper = DOM.$('.input-wrapper');
        const textarea = DOM.byId('message-input');

        if (!inputWrapper || !textarea || DOM.byId('autocorrect-btn')) return;

        // Create the button
        const btn = document.createElement('button');
        btn.id = 'autocorrect-btn';
        btn.className = 'autocorrect-btn';
        btn.title = 'Auto-correct spelling & grammar (Ctrl+Shift+S)';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
            </svg>
        `;

        // Insert it after the attach-btn or before textarea
        const attachBtn = document.getElementById('attach-image-btn');
        if (attachBtn) {
            attachBtn.after(btn);
        } else {
            inputWrapper.prepend(btn);
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const btn = DOM.byId('autocorrect-btn');
        const textarea = DOM.byId('message-input');

        if (btn) {
            DOM.on(btn, 'click', () => this.correctText());
        }

        // Handle shortcut
        if (textarea) {
            DOM.on(textarea, 'keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                    e.preventDefault();
                    this.correctText();
                }
            });

            // Show/hide button based on input content
            DOM.on(textarea, 'input', () => {
                this.updateButtonVisibility();
            });
        }
    },

    /**
     * Update button visibility based on textarea content
     */
    updateButtonVisibility() {
        const btn = DOM.byId('autocorrect-btn');
        const textarea = DOM.byId('message-input');
        if (!btn || !textarea) return;

        if (textarea.value.trim().length > 3) {
            DOM.addClass(btn, 'visible');
        } else {
            DOM.removeClass(btn, 'visible');
        }
    },

    /**
     * Perform the correction
     */
    async correctText() {
        if (this.isCorrecting) return;

        const textarea = DOM.byId('message-input');
        const text = textarea ? textarea.value.trim() : '';

        if (!text) return;

        this.setLoading(true);

        try {
            const response = await API.post('/api/autocorrect', { text });

            if (response.corrected && response.corrected !== text) {
                this.applyCorrection(response.corrected);
            } else if (response.error) {
                console.error('AutoCorrect error:', response.error);
                this.showFeedback('error');
            } else {
                this.showFeedback('nothing');
            }
        } catch (error) {
            console.error('AutoCorrect failed:', error);
            this.showFeedback('error');
        } finally {
            this.setLoading(false);
        }
    },

    /**
     * Apply the corrected text to the textarea with animation
     */
    applyCorrection(corrected) {
        const textarea = DOM.byId('message-input');
        if (!textarea) return;

        // Add sparkle animation to the button
        const btn = DOM.byId('autocorrect-btn');
        if (btn) {
            DOM.addClass(btn, 'sparkle');
            setTimeout(() => DOM.removeClass(btn, 'sparkle'), 1000);
        }

        // Update textarea
        textarea.value = corrected;

        // Trigger auto-resize if exists in App
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';

        this.showFeedback('success');
    },

    /**
     * Set loading state
     */
    setLoading(loading) {
        this.isCorrecting = loading;
        const btn = DOM.byId('autocorrect-btn');
        if (btn) {
            if (loading) {
                DOM.addClass(btn, 'loading');
                btn.disabled = true;
            } else {
                DOM.removeClass(btn, 'loading');
                btn.disabled = false;
            }
        }
    },

    /**
     * Show brief feedback
     */
    showFeedback(type) {
        const btn = DOM.byId('autocorrect-btn');
        if (!btn) return;

        const color = type === 'success' ? 'var(--success)' :
            type === 'nothing' ? 'var(--text-muted)' :
                'var(--error)';

        const originalColor = btn.style.color;
        btn.style.color = color;

        setTimeout(() => {
            btn.style.color = originalColor;
        }, 1500);
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoCorrect;
}
window.AutoCorrect = AutoCorrect;
