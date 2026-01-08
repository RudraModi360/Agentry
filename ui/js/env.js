/**
 * ============================================================
 * AGENTRY - Production Environment Configuration
 * ============================================================
 * 
 * This file should be loaded BEFORE config.js in production.
 * It sets the backend URL for separate frontend/backend deployments.
 * 
 * Usage in HTML (add before config.js):
 *   <script src="js/env.js"></script>
 *   <script src="js/config.js"></script>
 * 
 * For Vercel deployment with environment variables:
 *   Replace the values below with your Azure backend URL
 *   or inject via build process.
 */

(function () {
    // ============================================================
    // CONFIGURATION - Update these for your deployment
    // ============================================================

    /**
     * Backend API URL
     * Set this to your Azure backend URL
     * Example: 'https://agentry-backend.azurewebsites.net'
     * 
     * Leave empty or undefined to use same-origin (when frontend and backend 
     * Set this to your backend URL
     * Example: 'http://localhost:8000'
     */
    window.AGENTRY_API_URL = 'http://localhost:8000';

    /**
     * WebSocket URL (Optional)
     * Usually derived automatically from AGENTRY_API_URL
     * Only set if your WebSocket endpoint is different
     * Example: 'wss://agentry-backend.azurewebsites.net'
     */
    // window.AGENTRY_WS_URL = '';

    // ============================================================
    // Auto-detection for development
    // ============================================================

    // log detection
    if (window.AGENTRY_API_URL) {
        console.log('[Agentry] Using backend:', window.AGENTRY_API_URL);
    } else {
        console.warn('[Agentry] No AGENTRY_API_URL configured - using same-origin');
    }
})();
