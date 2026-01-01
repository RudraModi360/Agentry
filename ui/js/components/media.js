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
        console.log('[Media] Adding new item:', item.id, item.url);

        // Avoid duplicates (using loose equality for potential string/number mismatch)
        if (this.mediaItems.some(existing => existing.id == item.id)) return;

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

        // Clear Recent
        const clearBtn = DOM.byId('clear-recent-media');
        if (clearBtn) {
            DOM.on(clearBtn, 'click', () => {
                if (confirm('Clear recent media items from this view? (Files remain on server)')) {
                    this.mediaItems = [];
                    this.renderSidebarMedia();
                    this.renderGallery();
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
            console.log('[Media] Loading media library...');
            const response = await API.get('/api/media');

            // Handle different response formats defensively
            if (response && response.media) {
                this.mediaItems = Array.isArray(response.media) ? response.media : [];
            } else if (Array.isArray(response)) {
                this.mediaItems = response;
            } else {
                this.mediaItems = [];
            }

            console.log(`[Media] Loaded ${this.mediaItems.length} items`);
            this.renderSidebarMedia();
        } catch (error) {
            AppConfig.log('Media', 'Error loading recent media', 'error');
            console.error('[Media] Failed to load library:', error);
        }
    },

    /**
     * Render media in sidebar library
     */
    renderSidebarMedia() {
        const container = DOM.byId('media-container');
        if (!container) return;
        console.log('[Media] Rendering sidebar with', this.mediaItems.length, 'total items');

        if (this.mediaItems.length === 0) {
            container.innerHTML = '<div class="no-media-text">No media uploaded yet</div>';
            return;
        }

        // Show only the 4 most recent items
        const recent = this.mediaItems.slice(0, 4);
        container.innerHTML = recent.map(item => {
            let dateStr = '';
            try {
                const date = item.created_at ? new Date(item.created_at.replace(' ', 'T')) : new Date();
                dateStr = date.toLocaleDateString([], {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                });
            } catch (e) { }

            return `
                <div class="media-item" onclick="Media.viewItem('${item.url}')">
                    <button class="media-delete-btn" onclick="event.stopPropagation(); Media.deleteItem(${item.id})" title="Delete media">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                    <img src="${item.url}" alt="${item.filename || 'Media'}" 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         loading="lazy">
                    <div class="media-fallback" style="display: none; height: 100%; width: 100%; flex-direction: column; align-items: center; justify-content: center; background: var(--bg-tertiary); padding: 8px;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 24px; height: 24px; margin-bottom: 4px; opacity: 0.5;">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                        </svg>
                        <span style="font-size: 10px; text-align: center; word-break: break-all;">${item.filename || 'Media'}</span>
                    </div>
                    <div class="media-info-overlay">
                        <div class="media-filename" style="font-size: 10px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 2px;">${item.filename || 'Media'}</div>
                        <div class="media-time">${dateStr}</div>
                    </div>
                </div>
            `;
        }).join('');
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

        console.log('[Media] Rendering gallery with', this.mediaItems.length, 'items');

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
            let dateStr = 'Unknown date';
            try {
                // Handle sqlite's "YYYY-MM-DD HH:MM:SS" format or ISO format
                const dateRaw = item.created_at;
                const date = dateRaw ? new Date(dateRaw.replace(' ', 'T')) : new Date();

                if (!isNaN(date.getTime())) {
                    dateStr = date.toLocaleDateString([], {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    });
                }
            } catch (e) {
                console.warn('[Media] Date parsing failed for item', item.id);
            }

            return `
                <div class="media-3d-card" id="gallery-media-${item.id}">
                    <div class="media-3d-card-inner">
                        <img src="${item.url}" alt="${item.filename || 'Media'}" 
                             onerror="this.src='https://via.placeholder.com/300?text=Error+Loading+Image'"
                             onclick="Media.viewItem('${item.url}')">
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
