/**
 * AGENTRY UI - API Utilities
 */

const API = {
    /**
     * Get headers with authorization
     */
    getHeaders(includeContentType = true) {
        const headers = {};
        const token = AppConfig.getAuthToken();

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }

        return headers;
    },

    /**
     * Make a fetch request with config
     */
    async request(endpoint, options = {}) {
        const url = AppConfig.getApiUrl(endpoint);

        const config = {
            ...options,
            headers: {
                ...this.getHeaders(options.body && typeof options.body === 'object'),
                ...options.headers
            }
        };

        // Stringify body if it's an object
        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        try {
            AppConfig.log('API', `${config.method || 'GET'} ${endpoint}`);

            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new APIError(response.status, error.detail || error.message || 'Request failed');
            }

            // Return JSON or text based on content type
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();
        } catch (error) {
            if (error instanceof APIError) throw error;

            AppConfig.log('API', 'Request error:', error);
            throw new APIError(0, error.message || 'Network error');
        }
    },

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    },

    /**
     * POST request
     */
    async post(endpoint, body = {}) {
        return this.request(endpoint, { method: 'POST', body });
    },

    /**
     * PUT request
     */
    async put(endpoint, body = {}) {
        return this.request(endpoint, { method: 'PUT', body });
    },

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    /**
     * Upload file
     */
    async upload(endpoint, file, fieldName = 'file') {
        const formData = new FormData();
        formData.append(fieldName, file);

        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
    }
};

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(status, message) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }

    isUnauthorized() {
        return this.status === 401;
    }

    isForbidden() {
        return this.status === 403;
    }

    isNotFound() {
        return this.status === 404;
    }

    isServerError() {
        return this.status >= 500;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, APIError };
}
window.API = API;
window.APIError = APIError;
