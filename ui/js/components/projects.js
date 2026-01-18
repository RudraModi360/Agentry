/**
 * AGENTRY UI - Projects Component
 * Handles project management, selection, and creation.
 */

const Projects = {
    elements: {},
    isOpen: false,
    projects: [],

    /**
     * Initialize projects component
     */
    init() {
        this.cacheElements();
        this.setupEventListeners();
        AppConfig.log('Projects', 'Initialized');
    },

    /**
     * Cache DOM elements
     */
    cacheElements() {
        this.elements = {
            overlay: DOM.byId('projects-modal-overlay'),
            closeBtn: DOM.byId('projects-modal-close-btn'),
            list: DOM.byId('projects-list'),
            createBtn: DOM.byId('create-project-btn'),
            createForm: DOM.byId('create-project-form'),
            cancelCreateBtn: DOM.byId('cancel-project-btn'),
            saveProjectBtn: DOM.byId('save-project-btn'),
            titleInput: DOM.byId('project-title'),
            goalInput: DOM.byId('project-goal')
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

        // Show/Hide create form
        if (this.elements.createBtn) {
            DOM.on(this.elements.createBtn, 'click', () => {
                DOM.toggle(this.elements.createForm, true, 'block');
                DOM.toggle(this.elements.createBtn, false);
            });
        }

        if (this.elements.cancelCreateBtn) {
            DOM.on(this.elements.cancelCreateBtn, 'click', () => {
                DOM.toggle(this.elements.createForm, false);
                DOM.toggle(this.elements.createBtn, true, 'flex');
                this.clearForm();
            });
        }

        // Save project
        if (this.elements.saveProjectBtn) {
            DOM.on(this.elements.saveProjectBtn, 'click', () => this.saveProject());
        }
    },

    /**
     * Open projects modal
     */
    async open() {
        DOM.addClass(this.elements.overlay, 'active');
        this.isOpen = true;
        await this.loadProjects();
    },

    /**
     * Close projects modal
     */
    close() {
        DOM.removeClass(this.elements.overlay, 'active');
        this.isOpen = false;
        // Also hide form if open
        DOM.toggle(this.elements.createForm, false);
        DOM.toggle(this.elements.createBtn, true, 'flex');
        this.clearForm();
    },

    /**
     * Clear the create project form
     */
    clearForm() {
        if (this.elements.titleInput) this.elements.titleInput.value = '';
        if (this.elements.goalInput) this.elements.goalInput.value = '';
    },

    /**
     * Load projects from API
     */
    async loadProjects() {
        if (!this.elements.list) return;

        try {
            this.elements.list.innerHTML = `
                <div class="loading-projects">
                    <div class="spinner-small"></div>
                    <span>Fetching your workspaces...</span>
                </div>
            `;

            const response = await API.get('/api/projects');
            this.projects = response.projects || [];
            this.renderProjects();
        } catch (error) {
            console.error('[Projects] Failed to load projects:', error);
            this.elements.list.innerHTML = `
                <div class="error-state">
                    <p>Failed to load projects. Ensure backend is running.</p>
                    <button onclick="Projects.loadProjects()">Retry</button>
                </div>
            `;
        }
    },

    /**
     * Render projects list
     */
    renderProjects() {
        if (!this.elements.list) return;

        if (this.projects.length === 0) {
            this.elements.list.innerHTML = `
                <div class="no-projects">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <p>No projects found. Create one to organize your work!</p>
                </div>
            `;
            return;
        }

        this.elements.list.innerHTML = this.projects.map(p => `
            <div class="project-item" data-id="${p.id}" onclick="Projects.selectProject('${p.id}')">
                <div class="project-item-info">
                    <div class="project-item-title">${p.title}</div>
                    <div class="project-item-goal">${p.goal || 'No goal set'}</div>
                </div>
                <div class="project-item-meta">
                    <span class="project-date">${new Date(p.updated_at).toLocaleDateString()}</span>
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                </div>
            </div>
        `).join('');
    },

    /**
     * Save a new project
     */
    async saveProject() {
        const title = this.elements.titleInput.value.trim();
        const goal = this.elements.goalInput.value.trim();

        if (!title) {
            if (window.Modals) Modals.showToast('Please enter a project title', 'error');
            return;
        }

        try {
            const btn = this.elements.saveProjectBtn;
            const originalText = btn.textContent;
            btn.textContent = 'Creating...';
            btn.disabled = true;

            const projectId = title.toLowerCase().replace(/\s+/g, '-') + '-' + Date.now();

            await API.post('/api/projects', {
                project_id: projectId,
                title: title,
                goal: goal,
                environment: '',
                key_files: []
            });

            if (window.Modals) Modals.showToast('Project created successfully', 'success');

            // UI flip back
            DOM.toggle(this.elements.createForm, false);
            DOM.toggle(this.elements.createBtn, true, 'flex');
            this.clearForm();

            // Reload list
            await this.loadProjects();
        } catch (error) {
            console.error('[Projects] Failed to create project:', error);
            if (window.Modals) Modals.showToast(error.message || 'Failed to create project', 'error');
        } finally {
            this.elements.saveProjectBtn.textContent = 'Create Project';
            this.elements.saveProjectBtn.disabled = false;
        }
    },

    /**
     * Select a project
     */
    async selectProject(projectId) {
        const project = this.projects.find(p => p.id === projectId);
        if (!project) return;

        try {
            // Update current agent config if needed
            await API.post('/api/agent-config', {
                agent_type: Storage.get(AppConfig.agents.storageKey, 'default'),
                mode: 'solo',
                project_id: projectId
            });

            if (window.Modals) Modals.showToast(`Selected project: ${project.title}`, 'success');
            this.close();

            // Optional: Start a new clean session for the project
            // if (window.Sessions) Sessions.createNew();

        } catch (error) {
            console.error('[Projects] Failed to select project:', error);
            if (window.Modals) Modals.showToast('Failed to switch project context', 'error');
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Projects;
}
window.Projects = Projects;
