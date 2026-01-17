/**
 * AGENTRY UI - Sidebar Component (Flowbite Style)
 * Fixed sidebar always visible
 */

const Sidebar = {
    elements: {},

    /**
     * Initialize sidebar
     */
    init() {
        this.cacheElements();
        this.restoreState();
        this.setupEventListeners();

        // Clear any inline styles from previous code
        this.clearInlineStyles();

        AppConfig.log('Sidebar', 'Initialized');
    },

    /**
     * Clear inline styles that may have been set by previous code
     */
    clearInlineStyles() {
        const allElements = document.querySelectorAll('.sidebar-logo-text, .menu-item-text');
        allElements.forEach(el => {
            el.style.display = '';  // Remove inline style, let CSS handle it
        });
    },

    /**
     * Cache DOM elements
     */
    cacheElements() {
        this.elements = {
            sidebar: DOM.byId('sidebar'),
            overlay: DOM.byId('sidebar-overlay'),
            menuBtn: DOM.byId('mobile-menu-btn'),
            sessionsContainer: DOM.byId('sessions-container'),
            logoNewChatBtn: DOM.byId('logo-new-chat-btn'),
            toggleBtn: DOM.byId('sidebar-toggle-btn')
        };
    },

    /**
     * Restore sidebar state from storage
     */
    restoreState() {
        // Only valid on desktop
        if (window.innerWidth >= 768) {
            const isCollapsed = Storage.get('sidebar-collapsed', false);
            if (isCollapsed) {
                DOM.addClass(this.elements.sidebar, 'collapsed');
            }
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Mobile menu button
        if (this.elements.menuBtn) {
            DOM.on(this.elements.menuBtn, 'click', () => this.toggleMobile());
        }

        // Sidebar toggle button (desktop)
        if (this.elements.toggleBtn) {
            DOM.on(this.elements.toggleBtn, 'click', () => {
                const isCollapsed = DOM.toggleClass(this.elements.sidebar, 'collapsed');
                Storage.set('sidebar-collapsed', isCollapsed);
            });
        }

        // Overlay click to close on mobile
        if (this.elements.overlay) {
            DOM.on(this.elements.overlay, 'click', () => this.closeMobile());
        }

        // Logo click behavior: toggle sidebar when collapsed, create new chat when expanded
        if (this.elements.logoNewChatBtn) {
            DOM.on(this.elements.logoNewChatBtn, 'click', () => {
                // If sidebar is collapsed, expand it instead of creating new chat
                if (DOM.hasClass(this.elements.sidebar, 'collapsed')) {
                    DOM.removeClass(this.elements.sidebar, 'collapsed');
                    Storage.set('sidebar-collapsed', false);
                } else {
                    // Sidebar is expanded, create new chat
                    if (typeof Sessions !== 'undefined' && Sessions.createNew) {
                        Sessions.createNew();
                    }
                }
            });
        }

        // ESC key to close on mobile
        DOM.on(document, 'keydown', (e) => {
            if (e.key === 'Escape' && this.isMobileOpen()) {
                this.closeMobile();
            }
        });
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
