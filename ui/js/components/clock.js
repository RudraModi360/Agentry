/**
 * AGENTRY UI - Clock Component
 */

const Clock = {
    intervalId: null,

    /**
     * Initialize clock widget
     */
    init() {
        if (!AppConfig.clock.enabled) return;

        this.update();
        this.intervalId = setInterval(() => this.update(), AppConfig.clock.updateInterval);

        AppConfig.log('Clock', 'Initialized');
    },

    /**
     * Update clock display
     */
    update() {
        const now = new Date();
        const localHours = now.getHours();

        // Update each timezone
        const timezones = AppConfig.clock.timezones;
        timezones.forEach((tz, index) => {
            const time = now.toLocaleTimeString('en-US', {
                timeZone: tz.id,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });

            const elementId = index === 0 ? 'clock-time-india' : 'clock-time-usa';
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = time;
            }
        });

        // Debug logging like remote
        console.log('Clock update:',
            document.getElementById('clock-time-india')?.textContent,
            document.getElementById('clock-time-usa')?.textContent
        );

        // Update greeting based on local time
        let greeting;
        if (localHours >= 5 && localHours < 12) {
            greeting = 'Good Morning';
        } else if (localHours >= 12 && localHours < 17) {
            greeting = 'Good Afternoon';
        } else if (localHours >= 17 && localHours < 21) {
            greeting = 'Good Evening';
        } else {
            greeting = 'Good Night';
        }
        DOM.text('clock-greeting', greeting);

        // Update date
        const dateStr = now.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric'
        });
        DOM.text('clock-date', dateStr);
    },

    /**
     * Stop clock updates
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },

    /**
     * Restart clock updates
     */
    restart() {
        this.stop();
        this.init();
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Clock;
}
window.Clock = Clock;
