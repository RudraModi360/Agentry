/**
 * AGENTRY UI - Media Library & Gallery Component
 * Handles historical media display, gallery view, and deletion
 */

const Media = {
    mediaItems: [],

    /**
     * Initialize media component
     */
    init() {
        this.setupEventListeners();
        this.loadRecentMedia();
        AppConfig.log('Media', 'Initialized');
    },

    /**
     * Add a new media item to the local state and re-render
     */
    addItem(item, prepend = true) {
        if (!item || !item.url) return;

        // Avoid duplicates
        if (this.mediaItems.some(existing => existing.id === item.id)) return;

        if (prepend) {
            this.mediaItems.unshift(item);
        } else {
            this.mediaItems.push(item);
        }

        // Re-render components
        this.renderSidebarMedia();

        const overlay = DOM.byId('media-gallery-overlay');
        if (overlay && overlay.classList.contains('active')) {
            this.renderGallery();
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const mediaToggle = DOM.byId('media-gallery-btn');
        const mediaWrapper = DOM.byId('media-library-wrapper');
        const viewAllBtn = DOM.byId('media-view-all-btn');
        const closeGalleryBtn = DOM.byId('close-media-gallery');
        const galleryOverlay = DOM.byId('media-gallery-overlay');

        // Sidebar Toggle
        if (mediaToggle && mediaWrapper) {
            DOM.on(mediaToggle, 'click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const isVisible = mediaWrapper.style.display !== 'none';
                mediaWrapper.style.display = isVisible ? 'none' : 'block';
                mediaToggle.classList.toggle('active', !isVisible);

                if (!isVisible) {
                    this.loadRecentMedia();
                }
            });
        }

        // View All / Open Gallery
        if (viewAllBtn) {
            DOM.on(viewAllBtn, 'click', (e) => {
                e.preventDefault();
                this.openGallery();
            });
        }

        // Close Gallery
        if (closeGalleryBtn) {
            DOM.on(closeGalleryBtn, 'click', () => this.closeGallery());
        }

        if (galleryOverlay) {
            DOM.on(galleryOverlay, 'click', (e) => {
                if (e.target === galleryOverlay) {
                    this.closeGallery();
                }
            });
        }

        // Escape key to close gallery
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && galleryOverlay && galleryOverlay.classList.contains('active')) {
                this.closeGallery();
            }
        });
    },

    /**
     * Load recent media for sidebar
     */
    async loadRecentMedia() {
        try {
            const response = await API.get('/api/media');
            this.mediaItems = response.media || [];
            this.renderSidebarMedia();
        } catch (error) {
            AppConfig.log('Media', 'Error loading recent media', 'error');
            console.error(error);
        }
    },

    /**
     * Render media in sidebar library
     */
    renderSidebarMedia() {
        const container = DOM.byId('media-container');
        if (!container) return;

        if (this.mediaItems.length === 0) {
            container.innerHTML = '<div class="no-media-text">No media uploaded yet</div>';
            return;
        }

        // Show only the 4 most recent items
        const recent = this.mediaItems.slice(0, 4);
        container.innerHTML = recent.map(item => `
            <div class="media-item" onclick="Media.viewItem('${item.url}')">
                <img src="${item.url}" alt="${item.filename || 'Media'}" loading="lazy">
            </div>
        `).join('');
    },

    /**
     * Open media gallery modal
     */
    openGallery() {
        const overlay = DOM.byId('media-gallery-overlay');
        if (!overlay) return;

        overlay.classList.add('active');
        this.renderGallery();
    },

    /**
     * Close media gallery modal
     */
    closeGallery() {
        const overlay = DOM.byId('media-gallery-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    },

    /**
     * Render full gallery masonry
     */
    renderGallery() {
        const masonry = DOM.byId('media-masonry');
        if (!masonry) return;

        if (this.mediaItems.length === 0) {
            masonry.innerHTML = `
                <div class="media-gallery-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <circle cx="8.5" cy="8.5" r="1.5"></circle>
                        <polyline points="21 15 16 10 5 21"></polyline>
                    </svg>
                    <p>No media files yet</p>
                </div>
            `;
            return;
        }

        masonry.innerHTML = this.mediaItems.map(item => {
            const date = new Date(item.created_at);
            const dateStr = date.toLocaleDateString([], {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            return `
                <div class="media-3d-card" id="gallery-media-${item.id}">
                    <div class="media-3d-card-inner">
                        <img src="${item.url}" alt="${item.filename || 'Media'}" onclick="Media.viewItem('${item.url}')">
                        <div class="media-3d-card-overlay">
                            <div class="media-3d-card-date">${dateStr}</div>
                            <div class="media-3d-card-actions">
                                <button class="media-3d-card-btn" onclick="Media.viewItem('${item.url}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                        <circle cx="12" cy="12" r="3"></circle>
                                    </svg>
                                    View
                                </button>
                                <button class="media-3d-card-btn delete" onclick="event.stopPropagation(); Media.deleteItem(${item.id})">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * View full size image
     */
    viewItem(url) {
        window.open(url, '_blank');
    },

    /**
     * Delete media item
     */
    async deleteItem(id) {
        if (!confirm('Are you sure you want to delete this media item?')) return;

        try {
            await API.delete(`/api/media/${id}`);
            // Remove from local array
            this.mediaItems = this.mediaItems.filter(item => item.id !== id);

            // Re-render
            this.renderSidebarMedia();
            const overlay = DOM.byId('media-gallery-overlay');
            if (overlay && overlay.classList.contains('active')) {
                this.renderGallery();
            }

            AppConfig.log('Media', `Deleted item ${id}`);
        } catch (error) {
            AppConfig.log('Media', 'Error deleting media item', 'error');
            alert('Failed to delete media item.');
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Media;
}
window.Media = Media;
