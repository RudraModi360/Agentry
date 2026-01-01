/**
 * AGENTRY UI - Resizable Navbar Component
 * Handles scroll-responsive animations and mobile menu functionality
 */

const ResizableNavbar = (function () {
    'use strict';

    // Configuration
    const CONFIG = {
        scrollThreshold: 100,
        animationDuration: 400
    };

    // State
    let state = {
        isScrolled: false,
        isMobileMenuOpen: false,
        initialized: false
    };

    // DOM Elements cache
    let elements = {
        navbar: null,
        navBody: null,
        mobileNav: null,
        mobileMenuToggle: null,
        mobileMenu: null,
        mobileBackdrop: null,
        navItems: []
    };

    /**
     * Initialize the navbar
     */
    function init() {
        if (state.initialized) return;

        // Cache DOM elements
        elements.navbar = document.querySelector('.resizable-navbar');
        elements.navBody = document.querySelector('.nav-body');
        elements.mobileNav = document.querySelector('.mobile-nav');
        elements.mobileMenuToggle = document.querySelector('.mobile-nav-toggle');
        elements.mobileMenu = document.querySelector('.mobile-nav-menu');
        elements.mobileBackdrop = document.querySelector('.mobile-menu-backdrop');
        elements.navItems = document.querySelectorAll('.nav-item-link');

        if (!elements.navbar) {
            console.warn('ResizableNavbar: Navbar element not found');
            return;
        }

        // Set up event listeners
        setupScrollListener();
        setupMobileMenuListener();
        setupNavItemHover();

        // Initial check
        handleScroll();

        state.initialized = true;
        console.log('ResizableNavbar: Initialized');
    }

    /**
     * Handle scroll events for responsive navbar
     */
    function setupScrollListener() {
        let ticking = false;

        window.addEventListener('scroll', function () {
            if (!ticking) {
                window.requestAnimationFrame(function () {
                    handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }

    /**
     * Process scroll position and update navbar state
     */
    function handleScroll() {
        const scrollY = window.scrollY || window.pageYOffset;
        const shouldBeScrolled = scrollY > CONFIG.scrollThreshold;

        if (shouldBeScrolled !== state.isScrolled) {
            state.isScrolled = shouldBeScrolled;
            updateNavbarState();
        }
    }

    /**
     * Update navbar visual state based on scroll position
     */
    function updateNavbarState() {
        if (elements.navBody) {
            elements.navBody.classList.toggle('scrolled', state.isScrolled);
        }
        if (elements.mobileNav) {
            elements.mobileNav.classList.toggle('scrolled', state.isScrolled);
        }
    }

    /**
     * Setup mobile menu toggle functionality
     */
    function setupMobileMenuListener() {
        if (elements.mobileMenuToggle) {
            elements.mobileMenuToggle.addEventListener('click', toggleMobileMenu);
        }

        if (elements.mobileBackdrop) {
            elements.mobileBackdrop.addEventListener('click', closeMobileMenu);
        }

        // Close menu when clicking on a nav link
        elements.navItems.forEach(item => {
            item.addEventListener('click', function () {
                if (state.isMobileMenuOpen) {
                    closeMobileMenu();
                }
            });
        });

        // Close on escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && state.isMobileMenuOpen) {
                closeMobileMenu();
            }
        });
    }

    /**
     * Toggle mobile menu visibility
     */
    function toggleMobileMenu() {
        state.isMobileMenuOpen = !state.isMobileMenuOpen;
        updateMobileMenuState();
    }

    /**
     * Open mobile menu
     */
    function openMobileMenu() {
        state.isMobileMenuOpen = true;
        updateMobileMenuState();
    }

    /**
     * Close mobile menu
     */
    function closeMobileMenu() {
        state.isMobileMenuOpen = false;
        updateMobileMenuState();
    }

    /**
     * Update mobile menu DOM based on state
     */
    function updateMobileMenuState() {
        if (elements.mobileMenu) {
            elements.mobileMenu.classList.toggle('open', state.isMobileMenuOpen);
        }
        if (elements.mobileBackdrop) {
            elements.mobileBackdrop.classList.toggle('open', state.isMobileMenuOpen);
        }
        if (elements.mobileMenuToggle) {
            // Update icon
            const menuIcon = elements.mobileMenuToggle.querySelector('.menu-icon');
            const closeIcon = elements.mobileMenuToggle.querySelector('.close-icon');

            if (menuIcon && closeIcon) {
                menuIcon.style.display = state.isMobileMenuOpen ? 'none' : 'block';
                closeIcon.style.display = state.isMobileMenuOpen ? 'block' : 'none';
            }
        }

        // Prevent body scroll when menu is open
        document.body.style.overflow = state.isMobileMenuOpen ? 'hidden' : '';
    }

    /**
     * Setup hover effects for nav items
     */
    function setupNavItemHover() {
        elements.navItems.forEach(item => {
            item.addEventListener('mouseenter', function () {
                // Add subtle scale effect
                this.style.transform = 'scale(1.02)';
            });

            item.addEventListener('mouseleave', function () {
                this.style.transform = 'scale(1)';
            });
        });
    }

    /**
     * Generate navbar HTML structure
     * @param {Object} options - Configuration options
     * @returns {string} HTML string
     */
    function generateNavbarHTML(options = {}) {
        const {
            logoSrc = null,
            logoText = 'Startup',
            navItems = [],
            buttons = [],
            fixed = false
        } = options;

        const logoIcon = logoSrc
            ? `<img src="${logoSrc}" alt="logo" width="30" height="30">`
            : `<svg class="navbar-logo-icon" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
               </svg>`;

        const navItemsHTML = navItems.map((item, idx) => `
            <a href="${item.link}" class="nav-item-link" data-idx="${idx}">
                <span class="nav-item-bg"></span>
                <span>${item.name}</span>
            </a>
        `).join('');

        const buttonsHTML = buttons.map(btn => `
            <a href="${btn.href || '#'}" class="navbar-btn ${btn.variant || 'primary'}" ${btn.onClick ? `onclick="${btn.onClick}"` : ''}>
                ${btn.text}
            </a>
        `).join('');

        const mobileNavItemsHTML = navItems.map(item => `
            <a href="${item.link}" class="nav-item-link">${item.name}</a>
        `).join('');

        const mobileButtonsHTML = buttons.map(btn => `
            <a href="${btn.href || '#'}" class="navbar-btn ${btn.variant || 'primary'}" ${btn.onClick ? `onclick="${btn.onClick}"` : ''}>
                ${btn.text}
            </a>
        `).join('');

        return `
            <div class="resizable-navbar ${fixed ? 'fixed' : ''}">
                <!-- Desktop Navigation -->
                <nav class="nav-body">
                    <a href="/" class="navbar-logo">
                        ${logoIcon}
                        <span class="navbar-logo-text">${logoText}</span>
                    </a>
                    <div class="nav-items-container">
                        ${navItemsHTML}
                    </div>
                    <div class="nav-buttons">
                        ${buttonsHTML}
                    </div>
                </nav>

                <!-- Mobile Navigation -->
                <nav class="mobile-nav">
                    <div class="mobile-nav-header">
                        <a href="/" class="navbar-logo">
                            ${logoIcon}
                            <span class="navbar-logo-text">${logoText}</span>
                        </a>
                        <button class="mobile-nav-toggle" aria-label="Toggle menu">
                            <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="3" y1="6" x2="21" y2="6"></line>
                                <line x1="3" y1="12" x2="21" y2="12"></line>
                                <line x1="3" y1="18" x2="21" y2="18"></line>
                            </svg>
                            <svg class="close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display: none;">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="mobile-nav-menu">
                        ${mobileNavItemsHTML}
                        <div class="mobile-nav-buttons">
                            ${mobileButtonsHTML}
                        </div>
                    </div>
                </nav>
            </div>
            <div class="mobile-menu-backdrop"></div>
        `;
    }

    /**
     * Create and insert navbar into the page
     * @param {string} targetSelector - CSS selector for target container
     * @param {Object} options - Navbar configuration
     */
    function create(targetSelector, options = {}) {
        const target = document.querySelector(targetSelector);
        if (!target) {
            console.error('ResizableNavbar: Target element not found:', targetSelector);
            return;
        }

        const html = generateNavbarHTML(options);
        target.insertAdjacentHTML('afterbegin', html);

        // Re-initialize after insertion
        state.initialized = false;
        init();
    }

    // Public API
    return {
        init,
        create,
        generateNavbarHTML,
        openMobileMenu,
        closeMobileMenu,
        toggleMobileMenu,
        getState: () => ({ ...state })
    };
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    ResizableNavbar.init();
});
