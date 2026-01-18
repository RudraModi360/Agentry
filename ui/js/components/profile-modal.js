/**
 * AGENTRY UI - Profile Modal Component
 * Handles user profile, password change, and SMTP settings
 */

const ProfileModal = {
    elements: {},
    isOpen: false,

    /**
     * Initialize profile modal
     */
    init() {
        this.cacheElements();
        this.setupEventListeners();
        AppConfig.log('ProfileModal', 'Initialized');
    },

    /**
     * Cache DOM elements
     */
    cacheElements() {
        this.elements = {
            overlay: DOM.byId('profile-modal-overlay'),
            closeBtn: DOM.byId('profile-modal-close-btn'),

            // Tabs
            tabs: DOM.$$('.profile-tab'),
            tabContents: DOM.$$('.profile-tab-content'),

            // Profile Info
            usernameInput: DOM.byId('profile-username'),
            emailInput: DOM.byId('profile-email'),
            createdAtInput: DOM.byId('profile-created-at'),
            saveProfileBtn: DOM.byId('save-profile-btn'),

            // Security
            currentPassword: DOM.byId('security-current-password'),
            newPassword: DOM.byId('security-new-password'),
            confirmPassword: DOM.byId('security-confirm-password'),
            changePasswordBtn: DOM.byId('change-password-btn'),

            // SMTP
            smtpHost: DOM.byId('smtp-host'),
            smtpPort: DOM.byId('smtp-port'),
            smtpUsername: DOM.byId('smtp-username'),
            smtpPassword: DOM.byId('smtp-password'),
            smtpUseTls: DOM.byId('smtp-use-tls'),
            saveSmtpBtn: DOM.byId('save-smtp-btn'),
            testSmtpBtn: DOM.byId('test-smtp-btn')
        };
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        if (!this.elements.overlay) return;

        // Close on overlay click
        DOM.on(this.elements.overlay, 'click', (e) => {
            if (e.target === this.elements.overlay) {
                this.close();
            }
        });

        // Close button
        if (this.elements.closeBtn) {
            DOM.on(this.elements.closeBtn, 'click', () => this.close());
        }

        // Tabs
        this.elements.tabs.forEach(tab => {
            DOM.on(tab, 'click', () => {
                this.switchTab(tab.dataset.tab);
            });
        });

        // Profile Save
        if (this.elements.saveProfileBtn) {
            DOM.on(this.elements.saveProfileBtn, 'click', () => this.saveProfile());
        }

        // Password Change
        if (this.elements.changePasswordBtn) {
            DOM.on(this.elements.changePasswordBtn, 'click', () => this.changePassword());
        }

        // SMTP Save
        if (this.elements.saveSmtpBtn) {
            DOM.on(this.elements.saveSmtpBtn, 'click', () => this.saveSmtpSettings());
        }

        if (this.elements.testSmtpBtn) {
            DOM.on(this.elements.testSmtpBtn, 'click', () => this.testSmtp());
        }
    },

    /**
     * Open profile modal
     */
    open() {
        this.loadProfileData();
        DOM.addClass(this.elements.overlay, 'active');
        this.isOpen = true;
    },

    /**
     * Close profile modal
     */
    close() {
        DOM.removeClass(this.elements.overlay, 'active');
        this.isOpen = false;
        // Clear sensitive inputs
        if (this.elements.currentPassword) this.elements.currentPassword.value = '';
        if (this.elements.newPassword) this.elements.newPassword.value = '';
        if (this.elements.confirmPassword) this.elements.confirmPassword.value = '';
    },

    /**
     * Switch tab
     */
    switchTab(tabName) {
        // Update tab buttons
        this.elements.tabs.forEach(tab => {
            if (tab.dataset.tab === tabName) {
                DOM.addClass(tab, 'active');
            } else {
                DOM.removeClass(tab, 'active');
            }
        });

        // Update content
        this.elements.tabContents.forEach(content => {
            if (content.id === `tab-${tabName}`) {
                DOM.addClass(content, 'active');
            } else {
                DOM.removeClass(content, 'active');
            }
        });
    },

    /**
     * Load user profile data
     */
    async loadProfileData() {
        try {
            const user = await API.get('/api/auth/me');
            if (user && user.user) {
                if (this.elements.usernameInput) this.elements.usernameInput.value = user.user.username;
                if (this.elements.emailInput) this.elements.emailInput.value = user.user.email || '';
                if (this.elements.createdAtInput) this.elements.createdAtInput.value = new Date(user.user.created_at).toLocaleDateString();
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
            if (window.Modals) Modals.showToast('Failed to load profile data', 'error');
        }
    },

    /**
     * Save profile changes
     */
    async saveProfile() {
        const username = this.elements.usernameInput.value.trim();
        const email = this.elements.emailInput.value.trim();

        // Basic validation
        if (!username) {
            if (window.Modals) Modals.showToast('Username cannot be empty', 'error');
            return;
        }

        if (email && !email.includes('@')) {
            if (window.Modals) Modals.showToast('Invalid email address', 'error');
            return;
        }

        try {
            const btn = this.elements.saveProfileBtn;
            const originalText = btn.textContent;
            btn.textContent = 'Saving...';
            btn.disabled = true;

            await API.post('/api/auth/profile', { username, email });

            if (window.Modals) Modals.showToast('Profile updated successfully', 'success');

            // Update UI username if it changed
            const userNameEl = DOM.byId('user-name');
            if (userNameEl) userNameEl.textContent = username;

        } catch (error) {
            console.error('Failed to save profile:', error);
            if (window.Modals) Modals.showToast(error.message || 'Failed to update profile', 'error');
        } finally {
            const btn = this.elements.saveProfileBtn;
            btn.textContent = 'Save Profile';
            btn.disabled = false;
        }
    },

    /**
     * Change Password
     */
    async changePassword() {
        const currentPassword = this.elements.currentPassword.value;
        const newPassword = this.elements.newPassword.value;
        const confirmPassword = this.elements.confirmPassword.value;

        if (!currentPassword || !newPassword) {
            Modals.showToast('Please fill in all password fields', 'error');
            return;
        }

        if (newPassword !== confirmPassword) {
            Modals.showToast('New passwords do not match', 'error');
            return;
        }

        if (newPassword.length < 6) {
            Modals.showToast('Password must be at least 6 characters', 'error');
            return;
        }

        try {
            const btn = this.elements.changePasswordBtn;
            btn.textContent = 'Updating...';
            btn.disabled = true;

            await API.post('/api/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            Modals.showToast('Password changed successfully', 'success');
            // Clear inputs
            this.elements.currentPassword.value = '';
            this.elements.newPassword.value = '';
            this.elements.confirmPassword.value = '';
        } catch (error) {
            console.error('Failed to change password:', error);
            Modals.showToast(error.message || 'Failed to change password', 'error');
        } finally {
            const btn = this.elements.changePasswordBtn;
            btn.textContent = 'Update Password';
            btn.disabled = false;
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProfileModal;
}
window.ProfileModal = ProfileModal;
