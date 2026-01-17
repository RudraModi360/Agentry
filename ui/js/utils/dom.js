/**
 * AGENTRY UI - DOM Utilities
 */

const DOM = {
    /**
     * Shorthand for querySelector
     */
    $(selector, parent = document) {
        return parent.querySelector(selector);
    },

    /**
     * Shorthand for querySelectorAll (returns array)
     */
    $$(selector, parent = document) {
        return Array.from(parent.querySelectorAll(selector));
    },

    /**
     * Get element by ID
     */
    byId(id) {
        return document.getElementById(id);
    },

    /**
     * Create element with attributes and children
     */
    create(tag, attrs = {}, children = []) {
        const el = document.createElement(tag);

        for (const [key, value] of Object.entries(attrs)) {
            if (key === 'class' || key === 'className') {
                el.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(el.style, value);
            } else if (key.startsWith('on') && typeof value === 'function') {
                el.addEventListener(key.slice(2).toLowerCase(), value);
            } else if (key === 'data' && typeof value === 'object') {
                for (const [dataKey, dataValue] of Object.entries(value)) {
                    el.dataset[dataKey] = dataValue;
                }
            } else {
                el.setAttribute(key, value);
            }
        }

        children.forEach(child => {
            if (typeof child === 'string') {
                el.appendChild(document.createTextNode(child));
            } else if (child instanceof Node) {
                el.appendChild(child);
            }
        });

        return el;
    },

    /**
     * Set HTML content safely
     */
    html(el, content) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.innerHTML = content;
        return el;
    },

    /**
     * Set text content
     */
    text(el, content) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.textContent = content;
        return el;
    },

    /**
     * Add class(es) to element
     */
    addClass(el, ...classes) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.classList.add(...classes);
        return el;
    },

    /**
     * Remove class(es) from element
     */
    removeClass(el, ...classes) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.classList.remove(...classes);
        return el;
    },

    /**
     * Toggle class on element
     */
    toggleClass(el, className, force) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.classList.toggle(className, force);
        return el;
    },

    /**
     * Check if element has class
     */
    hasClass(el, className) {
        if (typeof el === 'string') el = this.byId(el);
        return el ? el.classList.contains(className) : false;
    },

    /**
     * Show element
     */
    show(el, display = '') {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.style.display = display;
        return el;
    },

    /**
     * Hide element
     */
    hide(el) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.style.display = 'none';
        return el;
    },

    /**
     * Toggle element visibility
     */
    toggle(el, show, display = 'block') {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.style.display = show ? (display || 'block') : 'none';
        return el;
    },

    /**
     * Add event listener
     */
    on(el, event, handler, options) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.addEventListener(event, handler, options);
        return el;
    },

    /**
     * Remove event listener
     */
    off(el, event, handler, options) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) el.removeEventListener(event, handler, options);
        return el;
    },

    /**
     * Delegate event handling
     */
    delegate(parent, event, selector, handler) {
        if (typeof parent === 'string') parent = this.byId(parent);
        if (!parent) return;

        parent.addEventListener(event, (e) => {
            const target = e.target.closest(selector);
            if (target && parent.contains(target)) {
                handler.call(target, e);
            }
        });
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Scroll element to bottom
     */
    scrollToBottom(el, smooth = true) {
        if (typeof el === 'string') el = this.byId(el);
        if (el) {
            el.scrollTo({
                top: el.scrollHeight,
                behavior: smooth ? 'smooth' : 'auto'
            });
        }
    },

    /**
     * Check if element is scrolled near bottom
     */
    isNearBottom(el, threshold = 100) {
        if (typeof el === 'string') el = this.byId(el);
        if (!el) return true;
        return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    },

    /**
     * Wait for DOM to be ready
     */
    ready(callback) {
        if (document.readyState !== 'loading') {
            callback();
        } else {
            document.addEventListener('DOMContentLoaded', callback);
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DOM;
}
window.DOM = DOM;
