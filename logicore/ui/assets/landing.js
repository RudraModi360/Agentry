/**
 * AGENTRY - Landing Page JavaScript
 * Modular JS for theme, orb background, and interactions
 */

// ========== Theme Management ==========
const ThemeManager = {
    storageKey: 'agentry-theme',
    html: document.documentElement,

    init() {
        const saved = localStorage.getItem(this.storageKey);
        const theme = saved || (this.getSystemTheme());
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
    }
};

// ========== Orb Background Effect ==========
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

        this.orbs = colors.map((color, i) => ({
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            targetX: Math.random() * this.canvas.width,
            targetY: Math.random() * this.canvas.height,
            radius: 250 + Math.random() * 150,
            color: color,
            speed: 0.02 + Math.random() * 0.02,
            mouseInfluence: 0.03 + Math.random() * 0.02,
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

        this.orbs.forEach((orb, i) => {
            // Subtle mouse influence
            orb.targetX += (this.mouse.x - this.canvas.width / 2) * orb.mouseInfluence * 0.01;
            orb.targetY += (this.mouse.y - this.canvas.height / 2) * orb.mouseInfluence * 0.01;

            // Keep orbs in bounds
            orb.targetX = Math.max(0, Math.min(this.canvas.width, orb.targetX));
            orb.targetY = Math.max(0, Math.min(this.canvas.height, orb.targetY));

            // Smooth movement
            orb.x += (orb.targetX - orb.x) * orb.speed;
            orb.y += (orb.targetY - orb.y) * orb.speed;

            // Random wandering
            if (Math.random() < 0.01) {
                orb.targetX = Math.random() * this.canvas.width;
                orb.targetY = Math.random() * this.canvas.height;
            }

            // Draw orb with gradient
            const gradient = this.ctx.createRadialGradient(
                orb.x, orb.y, 0,
                orb.x, orb.y, orb.radius
            );

            const alpha = isDark ? 0.15 : 0.25;
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

// ========== Initialize on DOM Ready ==========
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    OrbBackground.init('orb-canvas');

    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => ThemeManager.toggle());
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
