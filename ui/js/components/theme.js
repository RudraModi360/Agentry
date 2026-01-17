/**
 * AGENTRY UI - Theme Component
 */

const Theme = {
    storageKey: 'agentry-theme',

    /**
     * Initialize theme system
     */
    init() {
        // Apply saved or system theme immediately
        this.apply(this.getCurrent());

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.storageKey)) {
                this.apply(e.matches ? 'dark' : 'light');
            }
        });

        // Setup toggle button
        const toggleBtn = DOM.byId('theme-toggle-btn');
        if (toggleBtn) {
            DOM.on(toggleBtn, 'click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggle();
            });
        }

        AppConfig.log('Theme', 'Initialized with theme:', this.getCurrent());
    },

    /**
     * Get system preferred theme
     */
    getSystem() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    /**
     * Get current theme
     */
    getCurrent() {
        return localStorage.getItem(this.storageKey) || this.getSystem();
    },

    /**
     * Apply a theme
     */
    apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        // Dispatch event for other components to react
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    },

    /**
     * Set and save theme
     */
    set(theme) {
        localStorage.setItem(this.storageKey, theme);
        this.apply(theme);
        AppConfig.log('Theme', 'Set to:', theme);
    },

    /**
     * Toggle between light and dark
     */
    toggle() {
        const current = this.getCurrent();
        const next = current === 'dark' ? 'light' : 'dark';
        this.set(next);
    },

    /**
     * Check if dark mode is active
     */
    isDark() {
        return this.getCurrent() === 'dark';
    },

    /**
     * Reset to system preference
     */
    reset() {
        localStorage.removeItem(this.storageKey);
        this.apply(this.getSystem());
    }
};

// Apply theme immediately (before DOM ready) to prevent flash
(function () {
    const savedTheme = localStorage.getItem('agentry-theme');
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const theme = savedTheme || systemTheme;
    document.documentElement.setAttribute('data-theme', theme);
})();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Theme;
}
window.Theme = Theme;
