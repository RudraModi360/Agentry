/**
 * AGENTRY UI - Storage Utilities
 */

const Storage = {
    /**
     * Get item from localStorage with JSON parsing
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            if (item === null) return defaultValue;
            return JSON.parse(item);
        } catch {
            return localStorage.getItem(key) || defaultValue;
        }
    },

    /**
     * Set item in localStorage with JSON stringify
     */
    set(key, value) {
        try {
            const item = typeof value === 'string' ? value : JSON.stringify(value);
            localStorage.setItem(key, item);
            return true;
        } catch (e) {
            console.error('Storage.set error:', e);
            return false;
        }
    },

    /**
     * Remove item from localStorage
     */
    remove(key) {
        localStorage.removeItem(key);
    },

    /**
     * Clear all items from localStorage
     */
    clear() {
        localStorage.clear();
    },

    /**
     * Check if key exists in localStorage
     */
    has(key) {
        return localStorage.getItem(key) !== null;
    },

    /**
     * Get all keys in localStorage matching a prefix
     */
    keys(prefix = '') {
        const allKeys = Object.keys(localStorage);
        if (!prefix) return allKeys;
        return allKeys.filter(key => key.startsWith(prefix));
    },

    /**
     * Session storage get
     */
    sessionGet(key, defaultValue = null) {
        try {
            const item = sessionStorage.getItem(key);
            if (item === null) return defaultValue;
            return JSON.parse(item);
        } catch {
            return sessionStorage.getItem(key) || defaultValue;
        }
    },

    /**
     * Session storage set
     */
    sessionSet(key, value) {
        try {
            const item = typeof value === 'string' ? value : JSON.stringify(value);
            sessionStorage.setItem(key, item);
            return true;
        } catch (e) {
            console.error('Storage.sessionSet error:', e);
            return false;
        }
    },

    /**
     * Session storage remove
     */
    sessionRemove(key) {
        sessionStorage.removeItem(key);
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Storage;
}
window.Storage = Storage;
