/**
 * AGENTRY UI - Sidebar Component
 */

const Sidebar = {
    isCollapsed: false,
    isResizing: false,
    currentWidth: 280,

    elements: {},

    /**
     * Initialize sidebar
     */
    init() {
        this.cacheElements();
        this.loadState();
        this.setupEventListeners();
        this.setupResizer();

        AppConfig.log('Sidebar', 'Initialized');
    },

    /**
     * Cache DOM elements
     */
    cacheElements() {
        this.elements = {
            sidebar: DOM.byId('sidebar'),
            overlay: DOM.byId('sidebar-overlay'),
            collapseBtn: DOM.byId('sidebar-collapse-btn'),
            expandBtn: DOM.byId('sidebar-expand-btn'),
            resizer: DOM.byId('sidebar-resizer'),
            menuBtn: DOM.byId('menu-btn'),
            sessionsContainer: DOM.byId('sessions-container')
        };
    },

    /**
     * Load sidebar state from storage
     */
    loadState() {
        const state = Storage.get(AppConfig.sidebar.storageKey, {
            collapsed: false,
            width: AppConfig.sidebar.defaultWidth
        });

        this.currentWidth = state.width || AppConfig.sidebar.defaultWidth;

        if (state.collapsed) {
            this.collapse(false);
        } else {
            this.updateWidth();
        }
    },

    /**
     * Save sidebar state to storage
     */
    saveState() {
        Storage.set(AppConfig.sidebar.storageKey, {
            collapsed: this.isCollapsed,
            width: this.currentWidth
        });
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Collapse button
        if (this.elements.collapseBtn) {
            DOM.on(this.elements.collapseBtn, 'click', () => this.collapse());
        }

        // Expand button
        if (this.elements.expandBtn) {
            DOM.on(this.elements.expandBtn, 'click', () => this.expand());
        }

        // Mobile menu button
        if (this.elements.menuBtn) {
            DOM.on(this.elements.menuBtn, 'click', () => this.toggleMobile());
        }

        // Overlay click to close on mobile
        if (this.elements.overlay) {
            DOM.on(this.elements.overlay, 'click', () => this.closeMobile());
        }

        // ESC key to close on mobile
        DOM.on(document, 'keydown', (e) => {
            if (e.key === 'Escape' && this.isMobileOpen()) {
                this.closeMobile();
            }
        });
    },

    /**
     * Setup resizer
     */
    setupResizer() {
        if (!this.elements.resizer) return;

        const onMouseMove = (e) => {
            if (!this.isResizing) return;

            const width = e.clientX;
            const minWidth = AppConfig.sidebar.minWidth;
            const maxWidth = AppConfig.sidebar.maxWidth;

            this.currentWidth = Math.max(minWidth, Math.min(maxWidth, width));
            this.updateWidth();
        };

        const onMouseUp = () => {
            this.isResizing = false;
            DOM.removeClass(this.elements.resizer, 'active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            this.saveState();
        };

        DOM.on(this.elements.resizer, 'mousedown', (e) => {
            e.preventDefault();
            this.isResizing = true;
            DOM.addClass(this.elements.resizer, 'active');
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
        });

        DOM.on(document, 'mousemove', onMouseMove);
        DOM.on(document, 'mouseup', onMouseUp);
    },

    /**
     * Update sidebar width
     */
    updateWidth() {
        if (this.elements.sidebar && !this.isCollapsed) {
            this.elements.sidebar.style.width = `${this.currentWidth}px`;
        }
    },

    /**
     * Collapse sidebar
     */
    collapse(animate = true) {
        this.isCollapsed = true;

        if (this.elements.sidebar) {
            DOM.addClass(this.elements.sidebar, 'collapsed');
            if (!animate) {
                this.elements.sidebar.style.transition = 'none';
                requestAnimationFrame(() => {
                    this.elements.sidebar.style.transition = '';
                });
            }
        }

        DOM.addClass(document.body, 'sidebar-collapsed');
        this.saveState();
    },

    /**
     * Expand sidebar
     */
    expand() {
        this.isCollapsed = false;

        if (this.elements.sidebar) {
            DOM.removeClass(this.elements.sidebar, 'collapsed');
            this.updateWidth();
        }

        DOM.removeClass(document.body, 'sidebar-collapsed');
        this.saveState();
    },

    /**
     * Toggle sidebar collapse
     */
    toggle() {
        if (this.isCollapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    },

    /**
     * Toggle mobile sidebar
     */
    toggleMobile() {
        if (this.isMobileOpen()) {
            this.closeMobile();
        } else {
            this.openMobile();
        }
    },

    /**
     * Open mobile sidebar
     */
    openMobile() {
        DOM.addClass(this.elements.sidebar, 'open');
        DOM.addClass(this.elements.overlay, 'active');
        document.body.style.overflow = 'hidden';
    },

    /**
     * Close mobile sidebar
     */
    closeMobile() {
        DOM.removeClass(this.elements.sidebar, 'open');
        DOM.removeClass(this.elements.overlay, 'active');
        document.body.style.overflow = '';
    },

    /**
     * Check if mobile sidebar is open
     */
    isMobileOpen() {
        return DOM.hasClass(this.elements.sidebar, 'open');
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Sidebar;
}
window.Sidebar = Sidebar;
