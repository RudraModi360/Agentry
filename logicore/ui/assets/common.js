/**
 * AGENTRY - Common JavaScript
 * Shared utilities for theme management and orb background
 */

// ========== Theme Manager ==========
const ThemeManager = {
    storageKey: 'agentry-theme',
    html: document.documentElement,

    init() {
        const saved = localStorage.getItem(this.storageKey);
        const theme = saved || this.getSystemTheme();
        this.setTheme(theme);

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.storageKey)) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    },

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    setTheme(theme) {
        this.html.setAttribute('data-theme', theme);
        localStorage.setItem(this.storageKey, theme);
    },

    toggle() {
        const current = this.html.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },

    getTheme() {
        return this.html.getAttribute('data-theme') || 'light';
    }
};

// ========== Orb Background ==========
const OrbBackground = {
    canvas: null,
    ctx: null,
    orbs: [],
    mouse: { x: 0, y: 0 },
    animationId: null,

    init(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.resize();
        this.createOrbs();
        this.bindEvents();
        this.animate();
    },

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    },

    createOrbs() {
        const colors = [
            { h: 245, s: 80, l: 65 },  // Purple
            { h: 280, s: 70, l: 60 },  // Magenta
            { h: 200, s: 75, l: 55 },  // Cyan
        ];

        this.orbs = colors.map((color) => ({
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            targetX: Math.random() * this.canvas.width,
            targetY: Math.random() * this.canvas.height,
            radius: 200 + Math.random() * 150,
            color: color,
            speed: 0.015 + Math.random() * 0.015,
            mouseInfluence: 0.02 + Math.random() * 0.02,
        }));
    },

    bindEvents() {
        window.addEventListener('resize', () => this.resize());

        document.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
    },

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

        this.orbs.forEach((orb) => {
            // Subtle mouse influence
            orb.targetX += (this.mouse.x - this.canvas.width / 2) * orb.mouseInfluence * 0.008;
            orb.targetY += (this.mouse.y - this.canvas.height / 2) * orb.mouseInfluence * 0.008;

            // Keep orbs in bounds
            orb.targetX = Math.max(-orb.radius, Math.min(this.canvas.width + orb.radius, orb.targetX));
            orb.targetY = Math.max(-orb.radius, Math.min(this.canvas.height + orb.radius, orb.targetY));

            // Smooth movement
            orb.x += (orb.targetX - orb.x) * orb.speed;
            orb.y += (orb.targetY - orb.y) * orb.speed;

            // Random wandering
            if (Math.random() < 0.008) {
                orb.targetX = Math.random() * this.canvas.width;
                orb.targetY = Math.random() * this.canvas.height;
            }

            // Draw orb with gradient
            const gradient = this.ctx.createRadialGradient(
                orb.x, orb.y, 0,
                orb.x, orb.y, orb.radius
            );

            const alpha = isDark ? 0.12 : 0.2;
            gradient.addColorStop(0, `hsla(${orb.color.h}, ${orb.color.s}%, ${orb.color.l}%, ${alpha})`);
            gradient.addColorStop(1, `hsla(${orb.color.h}, ${orb.color.s}%, ${orb.color.l}%, 0)`);

            this.ctx.beginPath();
            this.ctx.arc(orb.x, orb.y, orb.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = gradient;
            this.ctx.fill();
        });

        this.animationId = requestAnimationFrame(() => this.animate());
    },

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
};

// ========== Initialize Common Features ==========
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();

    // Initialize orb background if canvas exists
    OrbBackground.init('orb-canvas');

    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => ThemeManager.toggle());
    }

    // Copy code button
    const copyCodeBtn = document.getElementById('copy-code-btn');
    const codeContent = document.getElementById('code-content');
    if (copyCodeBtn && codeContent) {
        copyCodeBtn.addEventListener('click', async () => {
            try {
                // Get plain text from the code content
                const text = codeContent.textContent || codeContent.innerText;
                await navigator.clipboard.writeText(text);

                // Visual feedback
                copyCodeBtn.classList.add('copied');
                const copyText = copyCodeBtn.querySelector('.copy-text');
                if (copyText) {
                    copyText.textContent = 'Copied!';
                }

                // Reset after 2 seconds
                setTimeout(() => {
                    copyCodeBtn.classList.remove('copied');
                    if (copyText) {
                        copyText.textContent = 'Copy';
                    }
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    }
});

// Export for use in other scripts
window.ThemeManager = ThemeManager;
window.OrbBackground = OrbBackground;
