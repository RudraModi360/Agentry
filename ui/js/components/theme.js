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

    set(theme) {
        localStorage.setItem(this.storageKey, theme);
        this.apply(theme);
        AppConfig.log('Theme', 'Set to:', theme);
    },

    /**
     * Update button icon based on theme
     */
    updateButtonIcon(theme) {
        const btn = DOM.byId('theme-toggle-btn');
        if (!btn) return;

        // If theme is dark, show Moon (to indicate current state) or Sun (to toggle)? 
        // Standard convention: Show the icon of the mode you will SWITCH TO, or the current mode representation?
        // ChatGPT shows the CURRENT mode icon usually, or a toggle. 
        // Let's show the ICON representing the CURRENT theme.
        // Dark theme -> Moon icon
        // Light theme -> Sun icon

        const isDark = theme === 'dark';

        if (isDark) {
            // Moon Icon
            btn.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
            btn.title = "Switch to Light Mode";
        } else {
            // Sun Icon
            btn.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
            btn.title = "Switch to Dark Mode";
        }
    },

    /**
     * Apply a theme
     */
    apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateButtonIcon(theme);

        // Dispatch event for other components to react
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
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
