/**
 * AGENTRY UI - Image Upload Component
 * Handles image selection, preview, and upload
 */

const ImageUpload = {
    selectedImages: [],

    /**
     * Initialize image upload component
     */
    init() {
        this.setupEventListeners();
        AppConfig.log('ImageUpload', 'Initialized');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const attachBtn = DOM.byId('attach-image-btn');
        const imageInput = DOM.byId('image-input');
        const inputWrapper = DOM.$('.input-wrapper');

        // Attach button click
        if (attachBtn) {
            DOM.on(attachBtn, 'click', () => {
                if (imageInput) {
                    imageInput.value = '';
                    imageInput.click();
                }
            });
        }

        // File selection
        if (imageInput) {
            DOM.on(imageInput, 'change', (e) => {
                const files = Array.from(e.target.files);
                const imageFiles = files.filter(f => f.type.startsWith('image/'));
                if (imageFiles.length > 0) {
                    this.handleSelect(imageFiles);
                }
            });
        }

        // Preview remove buttons (delegation)
        const previewWrapper = DOM.byId('images-preview-wrapper');
        if (previewWrapper) {
            DOM.on(previewWrapper, 'click', (e) => {
                if (e.target.closest('.image-preview-remove')) {
                    const btn = e.target.closest('.image-preview-remove');
                    const index = parseInt(btn.dataset.index);
                    this.remove(index);
                }
            });
        }

        // Drag and drop
        if (inputWrapper) {
            DOM.on(inputWrapper, 'dragover', (e) => {
                e.preventDefault();
                if (window.modelCapabilities?.supports_vision) {
                    inputWrapper.style.borderColor = 'var(--accent)';
                }
            });

            DOM.on(inputWrapper, 'dragleave', () => {
                inputWrapper.style.borderColor = '';
            });

            DOM.on(inputWrapper, 'drop', (e) => {
                e.preventDefault();
                inputWrapper.style.borderColor = '';

                if (!window.modelCapabilities?.supports_vision) return;

                const files = Array.from(e.dataTransfer.files);
                const imageFiles = files.filter(f => f.type.startsWith('image/'));
                if (imageFiles.length > 0) {
                    this.handleSelect(imageFiles);
                }
            });
        }
    },

    /**
     * Handle image file selection
     */
    handleSelect(files) {
        let processedCount = 0;

        files.forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.selectedImages.push(e.target.result);
                processedCount++;

                if (processedCount === files.length) {
                    this.renderPreviews();
                }
            };
            reader.readAsDataURL(file);
        });
    },

    /**
     * Render image previews
     */
    renderPreviews() {
        const wrapper = DOM.byId('images-preview-wrapper');
        const attachBtn = DOM.byId('attach-image-btn');

        if (!wrapper) return;

        wrapper.innerHTML = '';

        if (this.selectedImages.length === 0) {
            wrapper.style.display = 'none';
            if (attachBtn) attachBtn.classList.remove('has-image');
            this.updateSendButton();
            return;
        }

        wrapper.style.display = 'flex';
        if (attachBtn) attachBtn.classList.add('has-image');

        this.selectedImages.forEach((dataUrl, index) => {
            const item = DOM.create('div', { class: 'image-preview-item' });
            item.innerHTML = `
                <img src="${dataUrl}" alt="Preview ${index + 1}">
                <button class="image-preview-remove" data-index="${index}" title="Remove image">×</button>
            `;
            wrapper.appendChild(item);
        });

        this.updateSendButton();
    },

    /**
     * Remove image at index
     */
    remove(index) {
        this.selectedImages.splice(index, 1);
        this.renderPreviews();
    },

    /**
     * Clear all selected images
     */
    clear() {
        this.selectedImages = [];
        const imageInput = DOM.byId('image-input');
        if (imageInput) imageInput.value = '';
        this.renderPreviews();
    },

    /**
     * Update send button state
     */
    updateSendButton() {
        const messageInput = DOM.byId('message-input');
        const sendBtn = DOM.byId('send-btn');

        if (!messageInput || !sendBtn) return;

        const hasText = messageInput.value.trim().length > 0;
        const hasImages = this.selectedImages.length > 0;
        const isSendable = (hasText || hasImages) && App.state.isConnected;

        sendBtn.disabled = !isSendable;
    },

    /**
     * Get selected images data
     */
    getImages() {
        return [...this.selectedImages];
    },

    /**
     * Check if has images
     */
    hasImages() {
        return this.selectedImages.length > 0;
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageUpload;
}
window.ImageUpload = ImageUpload;
