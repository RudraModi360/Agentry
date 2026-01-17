/**
 * ============================================================
 * AGENTRY UI - Central Configuration
 * ============================================================
 * 
 * This file contains all configurable settings for the UI.
 * Modify these values to customize the application behavior
 * without touching individual component files.
 */

/**
 * Runtime configuration can be set before loading this script:
 * window.AGENTRY_API_URL = 'https://your-backend.azurewebsites.net';
 */

const AppConfig = {
    // ==================== API Configuration ====================
    api: {
        // Base URL for the backend API
        // Priority: window.AGENTRY_API_URL > empty string (same origin)
        baseUrl: window.AGENTRY_API_URL || '',

        // WebSocket URL (will be constructed from baseUrl if not explicitly set)
        wsUrl: window.AGENTRY_WS_URL || '',

        // Request timeout in milliseconds
        timeout: 30000,

        // Retry configuration
        retries: 3,
        retryDelay: 1000,
    },

    // ==================== Authentication ====================
    auth: {
        // LocalStorage key for auth token
        tokenKey: 'scratchy_token',

        // Login redirect path
        loginPath: '/login.html',

        // Default redirect after login
        defaultRedirect: '/chat.html',
    },

    // ==================== Theme Configuration ====================
    theme: {
        // LocalStorage key for theme preference
        storageKey: 'agentry-theme',

        // Default theme if none saved ('light', 'dark', or 'system')
        default: 'system',

        // Available themes
        options: ['light', 'dark'],
    },

    // ==================== Agent Configuration ====================
    agents: {
        // LocalStorage key for agent type
        storageKey: 'agentry-agent-type',

        // Default agent type
        default: 'default',

        // Available agent types and their configurations
        types: {
            default: {
                name: 'Default Agent',
                description: 'All tools + MCP servers for complex workflows',
                icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
                features: {
                    tools: true,
                    mcp: true,
                    vision: false,
                }
            },
            copilot: {
                name: 'Copilot Agent',
                description: 'Coding focused with file & execution tools',
                icon: 'M16 18l6-6-6-6M8 6l-6 6 6 6',
                features: {
                    tools: false,
                    mcp: false,
                    vision: true,
                }
            },
            smart: {
                name: 'Smart Agent',
                description: 'Enhanced reasoning & project context',
                icon: 'M9 18h6M10 22h4M12 2a7 7 0 017 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 01-1 1H9a1 1 0 01-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 017-7z',
                features: {
                    tools: false,
                    mcp: false,
                    vision: true,
                }
            }
        }
    },

    // ==================== Chat Configuration ====================
    chat: {
        // Maximum message length
        maxMessageLength: 100000,

        // Auto-scroll threshold (pixels from bottom)
        autoScrollThreshold: 100,

        // Message polling interval (ms) when WebSocket is down
        pollingInterval: 5000,
    },

    // ==================== Sidebar Configuration ====================
    sidebar: {
        // LocalStorage key for sidebar state
        storageKey: 'agentry-sidebar',

        // Default width in pixels
        defaultWidth: 280,

        // Minimum width in pixels
        minWidth: 200,

        // Maximum width in pixels
        maxWidth: 400,

        // Collapsed by default on mobile
        collapsedOnMobile: true,

        // Mobile breakpoint
        mobileBreakpoint: 768,
    },

    // ==================== Tools Configuration ====================
    tools: {
        // LocalStorage key for disabled tools
        disabledStorageKey: 'agentry-disabled-tools',

        // Tool approval timeout (seconds)
        approvalTimeout: 120,
    },

    // ==================== MCP Configuration ====================
    mcp: {
        // Status refresh interval (ms)
        statusRefreshInterval: 30000,

        // Connection timeout (ms)
        connectionTimeout: 10000,
    },

    // ==================== Media Configuration ====================
    media: {
        // Accepted image types
        acceptedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],

        // Maximum file size (bytes) - 10MB
        maxFileSize: 10 * 1024 * 1024,

        // Maximum images per message
        maxImagesPerMessage: 5,

        // Media storage path
        storagePath: '/media',
    },

    // ==================== Clock Widget ====================
    clock: {
        // Show clock widget in empty state
        enabled: true,

        // Update interval (ms)
        updateInterval: 1000,

        // Timezones to display
        timezones: [
            { id: 'Asia/Kolkata', label: 'India (IST)' },
            { id: 'America/Los_Angeles', label: 'California (PST)' },
        ],
    },

    // ==================== Animations ====================
    animations: {
        // Enable/disable all animations
        enabled: true,

        // Transition duration (ms)
        duration: 200,

        // Easing function
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },

    // ==================== Debug Mode ====================
    debug: {
        // Enable debug logging
        enabled: false,

        // Log WebSocket messages
        logWebSocket: false,

        // Log API requests
        logApi: false,
    },
};

// ==================== Helper Methods ====================

/**
 * Get the full API URL for an endpoint
 * @param {string} endpoint - API endpoint path
 * @returns {string} Full API URL
 */
AppConfig.getApiUrl = function (endpoint) {
    const base = this.api.baseUrl || '';
    return `${base}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
};

/**
 * Get WebSocket URL
 * @returns {string} WebSocket URL
 */
AppConfig.getWsUrl = function () {
    // Explicit WS URL takes highest priority
    if (this.api.wsUrl) {
        return this.api.wsUrl;
    }

    // Derive from API baseUrl if configured (for separate frontend/backend deployment)
    if (this.api.baseUrl) {
        const url = new URL(this.api.baseUrl);
        const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${url.host}`;
    }

    // Fallback to same origin
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
};

/**
 * Get auth token from storage
 * @returns {string|null} Auth token
 */
AppConfig.getAuthToken = function () {
    return localStorage.getItem(this.auth.tokenKey);
};

/**
 * Check if debug mode is enabled
 * @returns {boolean}
 */
AppConfig.isDebugEnabled = function () {
    return this.debug.enabled || localStorage.getItem('agentry-debug') === 'true';
};

/**
 * Debug log helper
 * @param {string} category - Log category
 * @param {...any} args - Log arguments
 */
AppConfig.log = function (category, ...args) {
    if (this.isDebugEnabled()) {
        console.log(`[${category}]`, ...args);
    }
};

// Freeze config to prevent accidental modifications
Object.freeze(AppConfig.api);
Object.freeze(AppConfig.auth);
Object.freeze(AppConfig.theme);
Object.freeze(AppConfig.agents.types);
Object.freeze(AppConfig.chat);
Object.freeze(AppConfig.sidebar);
Object.freeze(AppConfig.tools);
Object.freeze(AppConfig.mcp);
Object.freeze(AppConfig.media);
Object.freeze(AppConfig.clock);
Object.freeze(AppConfig.animations);
Object.freeze(AppConfig.debug);

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppConfig;
}

// Also expose globally for non-module scripts
window.AppConfig = AppConfig;
