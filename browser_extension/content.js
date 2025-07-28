// Prompt Manager Browser Extension - Content Script
class PromptManagerExtension {
    constructor() {
        this.apiUrl = 'http://localhost:5000/api';
        this.isEnabled = true;
        this.currentContext = {};
        this.widget = null;
        this.init();
    }

    async init() {
        // Load settings
        const settings = await chrome.storage.sync.get(['apiUrl', 'isEnabled']);
        this.apiUrl = settings.apiUrl || this.apiUrl;
        this.isEnabled = settings.isEnabled !== false;

        if (!this.isEnabled) return;

        // Check API connection and prompt for URL if needed
        const isConnected = await this.checkApiConnection();
        if (!isConnected) {
            await this.promptForApiUrl();
        }

        // Detect context and initialize
        this.detectContext();
        this.setupEventListeners();
        this.injectPromptWidget();
    }

    detectContext() {
        const url = window.location.href;
        const hostname = window.location.hostname;
        
        this.currentContext = {
            url: url,
            hostname: hostname,
            platform: this.getPlatform(hostname),
            textFields: this.findTextFields(),
            isAIChat: this.isAIChatInterface(),
            isCodeEditor: this.isCodeEditor(),
            pageContent: this.extractPageContent()
        };
    }

    getPlatform(hostname) {
        const platforms = {
            'claude.ai': 'claude',
            'chat.openai.com': 'chatgpt',
            'github.com': 'github',
            'docs.google.com': 'gdocs',
            'mail.google.com': 'gmail',
            'linear.app': 'linear',
            'notion.so': 'notion',
            'slack.com': 'slack'
        };
        
        return platforms[hostname] || 'unknown';
    }

    findTextFields() {
        const selectors = [
            'textarea',
            '[contenteditable="true"]',
            'input[type="text"]',
            '.ProseMirror', // Notion, Linear
            '#prompt-textarea', // Claude.ai
            '#composer', // Gmail
            '.ql-editor' // Various rich text editors
        ];

        const fields = [];
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(field => {
                if (this.isVisibleField(field)) {
                    fields.push(field);
                }
            });
        });

        return fields;
    }

    isVisibleField(element) {
        const rect = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);
        
        return rect.width > 50 && 
               rect.height > 20 && 
               style.display !== 'none' && 
               style.visibility !== 'hidden' &&
               style.opacity !== '0';
    }

    isAIChatInterface() {
        return ['claude.ai', 'chat.openai.com'].includes(window.location.hostname);
    }

    isCodeEditor() {
        return window.location.hostname === 'github.com' && 
               (window.location.pathname.includes('/edit/') || 
                document.querySelector('.monaco-editor'));
    }

    extractPageContent() {
        const title = document.title;
        const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
            .map(h => h.textContent.trim())
            .slice(0, 5);
        
        return {
            title,
            headings,
            hasErrors: this.detectErrors(),
            language: this.detectLanguage()
        };
    }

    detectErrors() {
        const errorKeywords = ['error', 'exception', 'failed', 'bug', 'issue'];
        const pageText = document.body.textContent.toLowerCase();
        
        return errorKeywords.some(keyword => pageText.includes(keyword));
    }

    detectLanguage() {
        if (window.location.hostname === 'github.com') {
            const langElement = document.querySelector('.BorderGrid-cell .text-bold');
            return langElement ? langElement.textContent.toLowerCase() : null;
        }
        return null;
    }

    setupEventListeners() {
        // Listen for focus on text fields
        document.addEventListener('focusin', (e) => {
            if (this.isRelevantTextField(e.target)) {
                this.showPromptSuggestions(e.target);
            }
        });

        // Listen for keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                e.preventDefault();
                this.togglePromptWidget();
            }
        });

        // Listen for context changes
        const observer = new MutationObserver(() => {
            this.detectContext();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    isRelevantTextField(element) {
        return this.currentContext.textFields.includes(element) ||
               element.matches('textarea, [contenteditable="true"]');
    }

    async showPromptSuggestions(targetElement) {
        if (!this.isEnabled) return;

        try {
            const suggestions = await this.getPromptSuggestions();
            this.displaySuggestions(suggestions, targetElement);
        } catch (error) {
            console.error('Failed to get prompt suggestions:', error);
        }
    }

    async getPromptSuggestions() {
        const context = {
            platform: this.currentContext.platform,
            has_error: this.currentContext.pageContent.hasErrors,
            is_planning: this.currentContext.pageContent.headings.some(h => 
                h.toLowerCase().includes('plan') || h.toLowerCase().includes('design')
            ),
            current_task: this.inferCurrentTask()
        };

        const response = await fetch(`${this.apiUrl}/prompts/suggest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ context })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async getTaskMasterProjects() {
        try {
            const response = await fetch(`${this.apiUrl}/projects`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch projects: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to fetch Task-Master projects:', error);
            return [];
        }
    }

    async getProjectContext(projectId) {
        try {
            const response = await fetch(`${this.apiUrl}/projects/${projectId}/context`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch project context: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to fetch project context:', error);
            return null;
        }
    }

    inferCurrentTask() {
        const title = this.currentContext.pageContent.title.toLowerCase();
        const headings = this.currentContext.pageContent.headings.join(' ').toLowerCase();
        const combined = `${title} ${headings}`;

        if (combined.includes('bug') || combined.includes('issue')) return 'debugging';
        if (combined.includes('feature') || combined.includes('implement')) return 'development';
        if (combined.includes('review') || combined.includes('pr')) return 'code review';
        if (combined.includes('test')) return 'testing';
        if (combined.includes('doc')) return 'documentation';
        
        return 'general';
    }

    displaySuggestions(suggestions, targetElement) {
        // Remove existing suggestions
        this.removeSuggestions();

        if (!suggestions || suggestions.length === 0) return;

        // Create suggestion popup
        const popup = document.createElement('div');
        popup.className = 'prompt-suggestions-popup';
        popup.innerHTML = `
            <div class="prompt-suggestions-header">
                <span class="prompt-icon">💡</span>
                <span>Suggested Prompts</span>
                <button class="close-btn">&times;</button>
            </div>
            <div class="prompt-suggestions-list">
                ${suggestions.slice(0, 5).map((prompt, index) => `
                    <div class="prompt-suggestion" data-prompt-id="${prompt.id}" data-index="${index}">
                        <div class="prompt-title">${prompt.title}</div>
                        <div class="prompt-meta">
                            <span class="prompt-category">${prompt.category}</span>
                            <span class="prompt-usage">Used ${prompt.used_count} times</span>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="prompt-suggestions-footer">
                <span class="shortcut-hint">Ctrl+Shift+P to toggle</span>
            </div>
        `;

        // Position popup near the target element
        const rect = targetElement.getBoundingClientRect();
        popup.style.position = 'fixed';
        popup.style.top = `${rect.bottom + 5}px`;
        popup.style.left = `${rect.left}px`;
        popup.style.zIndex = '10000';

        document.body.appendChild(popup);

        // Add event listeners
        popup.querySelector('.close-btn').addEventListener('click', () => {
            this.removeSuggestions();
        });

        popup.querySelectorAll('.prompt-suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', async () => {
                const promptId = suggestion.dataset.promptId;
                await this.usePrompt(promptId, targetElement);
                this.removeSuggestions();
            });
        });

        // Auto-hide after 10 seconds
        setTimeout(() => this.removeSuggestions(), 10000);
    }

    async usePrompt(promptId, targetElement) {
        try {
            // Get prompt details
            const response = await fetch(`${this.apiUrl}/prompts/${promptId}`);
            const prompt = await response.json();

            if (prompt.variables && prompt.variables.length > 0) {
                // Show variable input dialog
                this.showVariableDialog(prompt, targetElement);
            } else {
                // Use prompt directly
                this.insertPromptContent(prompt.content, targetElement);
            }
        } catch (error) {
            console.error('Failed to use prompt:', error);
            this.showNotification('Failed to load prompt', 'error');
        }
    }

    showVariableDialog(prompt, targetElement) {
        const dialog = document.createElement('div');
        dialog.className = 'prompt-variable-dialog';
        dialog.innerHTML = `
            <div class="dialog-content">
                <h3>Fill in variables for: ${prompt.title}</h3>
                <form class="variable-form">
                    ${prompt.variables.map(variable => `
                        <div class="variable-input">
                            <label for="var-${variable}">${variable}:</label>
                            <input type="text" id="var-${variable}" name="${variable}" 
                                   placeholder="Enter ${variable}...">
                        </div>
                    `).join('')}
                    <div class="dialog-buttons">
                        <button type="submit" class="use-prompt-btn">Use Prompt</button>
                        <button type="button" class="cancel-btn">Cancel</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(dialog);

        const form = dialog.querySelector('.variable-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const variables = {};
            prompt.variables.forEach(variable => {
                variables[variable] = form.querySelector(`#var-${variable}`).value;
            });

            try {
                const response = await fetch(`${this.apiUrl}/prompts/${prompt.id}/render`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ variables })
                });

                const result = await response.json();
                this.insertPromptContent(result.content, targetElement);
                document.body.removeChild(dialog);
            } catch (error) {
                console.error('Failed to render prompt:', error);
                this.showNotification('Failed to render prompt', 'error');
            }
        });

        dialog.querySelector('.cancel-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });
    }

    insertPromptContent(content, targetElement) {
        if (targetElement.tagName === 'TEXTAREA' || targetElement.tagName === 'INPUT') {
            targetElement.value = content;
            targetElement.dispatchEvent(new Event('input', { bubbles: true }));
        } else if (targetElement.isContentEditable) {
            targetElement.textContent = content;
            targetElement.dispatchEvent(new Event('input', { bubbles: true }));
        }

        // Copy to clipboard as backup
        navigator.clipboard.writeText(content);
        this.showNotification('Prompt inserted and copied to clipboard', 'success');
    }

    removeSuggestions() {
        const existing = document.querySelector('.prompt-suggestions-popup');
        if (existing) {
            existing.remove();
        }
    }

    injectPromptWidget() {
        // Create floating widget for quick access
        const widget = document.createElement('div');
        widget.className = 'prompt-manager-widget';
        widget.innerHTML = `
            <div class="widget-toggle" title="Prompt Manager (Ctrl+Shift+P)">
                💡
            </div>
        `;

        widget.addEventListener('click', () => {
            this.togglePromptWidget();
        });

        document.body.appendChild(widget);
        this.widget = widget;
    }

    togglePromptWidget() {
        // Implementation for toggle functionality
        const existingPopup = document.querySelector('.prompt-suggestions-popup');
        if (existingPopup) {
            this.removeSuggestions();
        } else {
            const activeElement = document.activeElement;
            if (this.isRelevantTextField(activeElement)) {
                this.showPromptSuggestions(activeElement);
            } else {
                this.showQuickPromptAccess();
            }
        }
    }

    showQuickPromptAccess() {
        // Show quick access without target element
        const popup = document.createElement('div');
        popup.className = 'prompt-quick-access';
        popup.innerHTML = `
            <div class="quick-access-header">
                <span>Quick Prompt Access</span>
                <button class="project-btn" title="Select Project">📂</button>
                <button class="close-btn">&times;</button>
            </div>
            <div class="quick-access-search">
                <input type="text" placeholder="Search prompts..." class="prompt-search">
            </div>
            <div class="quick-access-results"></div>
        `;

        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
        popup.style.zIndex = '10001';

        document.body.appendChild(popup);

        // Implement search functionality
        const searchInput = popup.querySelector('.prompt-search');
        searchInput.addEventListener('input', (e) => {
            this.searchPrompts(e.target.value, popup.querySelector('.quick-access-results'));
        });

        popup.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(popup);
        });

        popup.querySelector('.project-btn').addEventListener('click', () => {
            this.showProjectSelector();
        });

        searchInput.focus();
    }

    async showProjectSelector() {
        const projects = await this.getTaskMasterProjects();
        
        if (!projects || projects.length === 0) {
            this.showNotification('No Task-Master projects found', 'info');
            return;
        }

        // Remove existing popups
        document.querySelectorAll('.prompt-quick-access, .project-selector').forEach(el => el.remove());

        const selector = document.createElement('div');
        selector.className = 'project-selector';
        selector.innerHTML = `
            <div class="project-selector-header">
                <span>Select Task-Master Project</span>
                <button class="close-btn">&times;</button>
            </div>
            <div class="project-list">
                ${projects.map(project => `
                    <div class="project-item" data-project-id="${project.id}">
                        <div class="project-name">${project.name}</div>
                        <div class="project-path">${project.path}</div>
                        <div class="project-meta">
                            ${project.active ? '🟢 Active' : '⚫ Inactive'} • 
                            ${project.task_count} tasks • 
                            Branch: ${project.git_info?.branch || 'unknown'}
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="project-selector-footer">
                <button class="task-master-prompt-btn">Use Task-Master Prompt</button>
            </div>
        `;

        selector.style.position = 'fixed';
        selector.style.top = '50%';
        selector.style.left = '50%';
        selector.style.transform = 'translate(-50%, -50%)';
        selector.style.zIndex = '10002';

        document.body.appendChild(selector);

        let selectedProjectId = null;

        // Add click handlers for project items
        selector.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => {
                // Remove previous selection
                selector.querySelectorAll('.project-item').forEach(i => i.classList.remove('selected'));
                
                // Add selection to clicked item
                item.classList.add('selected');
                selectedProjectId = item.dataset.projectId;
                
                // Enable the Task-Master prompt button
                selector.querySelector('.task-master-prompt-btn').disabled = false;
            });
        });

        // Handle Task-Master prompt button
        selector.querySelector('.task-master-prompt-btn').addEventListener('click', async () => {
            if (!selectedProjectId) {
                this.showNotification('Please select a project first', 'error');
                return;
            }

            try {
                const context = await this.getProjectContext(selectedProjectId);
                if (context) {
                    await this.useTaskMasterPromptWithContext(context);
                    document.body.removeChild(selector);
                } else {
                    this.showNotification('Failed to get project context', 'error');
                }
            } catch (error) {
                console.error('Failed to use Task-Master prompt:', error);
                this.showNotification('Failed to use Task-Master prompt', 'error');
            }
        });

        selector.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(selector);
        });
    }

    async useTaskMasterPromptWithContext(context) {
        try {
            // Render the Task-Master prompt with project context
            const response = await fetch(`${this.apiUrl}/prompts/4/render`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ variables: context.variables })
            });

            if (!response.ok) {
                throw new Error(`Failed to render prompt: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Copy to clipboard and show notification
            await navigator.clipboard.writeText(result.content);
            this.showNotification(`Task-Master prompt ready for ${context.project_name}`, 'success');

        } catch (error) {
            console.error('Failed to use Task-Master prompt:', error);
            this.showNotification('Failed to prepare Task-Master prompt', 'error');
        }
    }

    async searchPrompts(query, resultsContainer) {
        try {
            const response = await fetch(`${this.apiUrl}/prompts?search=${encodeURIComponent(query)}`);
            const prompts = await response.json();

            resultsContainer.innerHTML = prompts.slice(0, 10).map(prompt => `
                <div class="search-result" data-prompt-id="${prompt.id}">
                    <div class="prompt-title">${prompt.title}</div>
                    <div class="prompt-category">${prompt.category}</div>
                </div>
            `).join('');

            resultsContainer.querySelectorAll('.search-result').forEach(result => {
                result.addEventListener('click', async () => {
                    const promptId = result.dataset.promptId;
                    await navigator.clipboard.writeText(await this.getPromptContent(promptId));
                    this.showNotification('Prompt copied to clipboard', 'success');
                    document.body.removeChild(document.querySelector('.prompt-quick-access'));
                });
            });
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    async getPromptContent(promptId) {
        const response = await fetch(`${this.apiUrl}/prompts/${promptId}`);
        const prompt = await response.json();
        return prompt.content;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `prompt-notification ${type}`;
        notification.textContent = message;

        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '10002';

        document.body.appendChild(notification);

        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 3000);
    }

    async checkApiConnection() {
        try {
            const healthUrl = this.apiUrl.replace('/api', '').replace(/\/$/, '') + '/health';
            const response = await fetch(healthUrl, { 
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async promptForApiUrl() {
        return new Promise((resolve) => {
            // Remove any existing dialogs
            document.querySelectorAll('.api-url-dialog').forEach(el => el.remove());

            const dialog = document.createElement('div');
            dialog.className = 'api-url-dialog';
            dialog.innerHTML = `
                <div style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.7);
                    z-index: 10002;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <div style="
                        background: white;
                        padding: 30px;
                        border-radius: 12px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                        max-width: 500px;
                        width: 90%;
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    ">
                        <div style="font-size: 24px; margin-bottom: 10px;">🧶</div>
                        <h2 style="margin: 0 0 10px 0; color: #333;">Prompt Manager Setup</h2>
                        <p style="color: #666; margin-bottom: 20px; line-height: 1.4;">
                            Can't connect to the Prompt Manager API server.<br>
                            Please start the server or enter a custom URL.
                        </p>
                        <div style="background: #f5f5f5; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-family: monospace; font-size: 13px;">
                            💡 To start the server: <strong>python3 src/prompt_api.py</strong>
                        </div>
                        <form class="api-url-form">
                            <input 
                                type="url" 
                                id="api-url-input"
                                placeholder="http://localhost:5000/api"
                                value="http://localhost:5000/api"
                                style="
                                    width: 100%;
                                    padding: 12px;
                                    border: 1px solid #ddd;
                                    border-radius: 6px;
                                    font-size: 14px;
                                    margin-bottom: 20px;
                                    box-sizing: border-box;
                                "
                            >
                            <div style="display: flex; gap: 10px; justify-content: center;">
                                <button type="button" class="test-connection-btn" style="
                                    background: #3b82f6;
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 14px;
                                ">🔍 Test Connection</button>
                                <button type="submit" style="
                                    background: #10b981;
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 14px;
                                ">✅ Use This URL</button>
                                <button type="button" class="skip-btn" style="
                                    background: #6b7280;
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 14px;
                                ">Skip</button>
                            </div>
                            <div class="status-message" style="margin-top: 15px; font-size: 14px;"></div>
                        </form>
                    </div>
                </div>
            `;

            document.body.appendChild(dialog);

            const form = dialog.querySelector('.api-url-form');
            const input = dialog.querySelector('#api-url-input');
            const testBtn = dialog.querySelector('.test-connection-btn');
            const skipBtn = dialog.querySelector('.skip-btn');
            const statusMsg = dialog.querySelector('.status-message');

            // Test connection button
            testBtn.addEventListener('click', async () => {
                const url = input.value.trim();
                if (!url) return;

                testBtn.textContent = '🔍 Testing...';
                testBtn.disabled = true;
                statusMsg.innerHTML = '';

                try {
                    const healthUrl = url.replace('/api', '').replace(/\/$/, '') + '/health';
                    const response = await fetch(healthUrl, { 
                        method: 'GET',
                        signal: AbortSignal.timeout(5000)
                    });
                    
                    if (response.ok) {
                        statusMsg.innerHTML = '<span style="color: #10b981;">✅ Connection successful!</span>';
                    } else {
                        statusMsg.innerHTML = '<span style="color: #ef4444;">❌ Server responded with error</span>';
                    }
                } catch (error) {
                    statusMsg.innerHTML = '<span style="color: #ef4444;">❌ Connection failed</span>';
                } finally {
                    testBtn.textContent = '🔍 Test Connection';
                    testBtn.disabled = false;
                }
            });

            // Form submit
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const url = input.value.trim();
                if (url) {
                    this.apiUrl = url;
                    await chrome.storage.sync.set({ apiUrl: url });
                }
                document.body.removeChild(dialog);
                resolve();
            });

            // Skip button
            skipBtn.addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve();
            });

            input.focus();
            input.select();
        });
    }

    // Handle context menu suggestions
    async handleContextMenuSuggestions(selectedText) {
        const activeElement = document.activeElement;
        if (this.isRelevantTextField(activeElement)) {
            await this.showPromptSuggestions(activeElement);
        } else {
            this.showNotification('Click on a text field first, then use context menu', 'info');
        }
    }

    // Handle saving selected text as prompt template
    async handleSaveAsTemplate(selectedText) {
        if (!selectedText || selectedText.trim().length === 0) {
            this.showNotification('No text selected to save as template', 'error');
            return;
        }

        this.showSaveTemplateDialog(selectedText);
    }

    // Show save template dialog
    showSaveTemplateDialog(content) {
        const dialog = document.createElement('div');
        dialog.className = 'save-template-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 10003;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    max-width: 600px;
                    width: 90%;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                ">
                    <h2 style="margin: 0 0 20px 0; color: #333;">💾 Save as Prompt Template</h2>
                    <form class="template-form">
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Title:</label>
                            <input type="text" name="title" placeholder="Enter prompt title..." style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid #ddd;
                                border-radius: 6px;
                                font-size: 14px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Category:</label>
                            <select name="category" style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid #ddd;
                                border-radius: 6px;
                                font-size: 14px;
                                box-sizing: border-box;
                            ">
                                <option value="user-generated">User Generated</option>
                                <option value="code-review">Code Review</option>
                                <option value="debugging">Debugging</option>
                                <option value="documentation">Documentation</option>
                                <option value="testing">Testing</option>
                                <option value="planning">Planning</option>
                                <option value="communication">Communication</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Tags (comma-separated):</label>
                            <input type="text" name="tags" placeholder="ai, development, workflow..." style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid #ddd;
                                border-radius: 6px;
                                font-size: 14px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Content Preview:</label>
                            <textarea readonly style="
                                width: 100%;
                                height: 100px;
                                padding: 10px;
                                border: 1px solid #ddd;
                                border-radius: 6px;
                                font-size: 12px;
                                font-family: monospace;
                                background: #f9f9f9;
                                box-sizing: border-box;
                                resize: vertical;
                            ">${content}</textarea>
                        </div>
                        <div style="display: flex; gap: 10px; justify-content: flex-end;">
                            <button type="button" class="cancel-btn" style="
                                background: #6b7280;
                                color: white;
                                border: none;
                                padding: 10px 20px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 14px;
                            ">Cancel</button>
                            <button type="submit" style="
                                background: #10b981;
                                color: white;
                                border: none;
                                padding: 10px 20px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 14px;
                            ">💾 Save Template</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        const form = dialog.querySelector('.template-form');
        const titleInput = form.querySelector('input[name="title"]');
        
        // Set default title based on content
        const defaultTitle = this.generateDefaultTitle(content);
        titleInput.value = defaultTitle;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const template = {
                title: formData.get('title'),
                content: content,
                category: formData.get('category'),
                tags: formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag)
            };

            try {
                const response = await chrome.runtime.sendMessage({
                    action: 'savePromptTemplate',
                    template: template
                });

                if (response.error) {
                    throw new Error(response.error);
                }

                this.showNotification(`✅ Template "${template.title}" saved successfully!`, 'success');
                document.body.removeChild(dialog);
            } catch (error) {
                console.error('Failed to save template:', error);
                this.showNotification('Failed to save template', 'error');
            }
        });

        dialog.querySelector('.cancel-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        titleInput.focus();
        titleInput.select();
    }

    // Generate default title from content
    generateDefaultTitle(content) {
        const firstLine = content.split('\n')[0].trim();
        if (firstLine.length > 50) {
            return firstLine.substring(0, 47) + '...';
        }
        return firstLine || 'Untitled Prompt';
    }

    // Handle showing recent prompts
    async handleShowRecentPrompts() {
        try {
            const response = await chrome.runtime.sendMessage({
                action: 'getRecentPrompts'
            });

            if (response.error) {
                throw new Error(response.error);
            }

            this.showRecentPromptsDialog(response.prompts);
        } catch (error) {
            console.error('Failed to get recent prompts:', error);
            this.showNotification('Failed to load recent prompts', 'error');
        }
    }

    // Show recent prompts dialog
    showRecentPromptsDialog(prompts) {
        const dialog = document.createElement('div');
        dialog.className = 'recent-prompts-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 10003;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    background: white;
                    padding: 0;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    max-width: 700px;
                    width: 90%;
                    max-height: 80vh;
                    overflow: hidden;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                ">
                    <div style="
                        padding: 20px 30px;
                        border-bottom: 1px solid #e5e7eb;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <h2 style="margin: 0; color: #333;">🕒 Recent Prompts</h2>
                        <button class="close-btn" style="
                            background: none;
                            border: none;
                            font-size: 24px;
                            cursor: pointer;
                            color: #6b7280;
                        ">&times;</button>
                    </div>
                    <div style="
                        max-height: 400px;
                        overflow-y: auto;
                        padding: 0;
                    ">
                        ${prompts.length === 0 ? `
                            <div style="padding: 40px; text-align: center; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
                                <p>No recent prompts found</p>
                            </div>
                        ` : prompts.map(prompt => `
                            <div class="recent-prompt-item" data-prompt-id="${prompt.id}" style="
                                padding: 16px 30px;
                                border-bottom: 1px solid #f3f4f6;
                                cursor: pointer;
                                transition: background-color 0.2s;
                            " onmouseover="this.style.backgroundColor='#f9fafb'" onmouseout="this.style.backgroundColor='white'">
                                <div style="
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: flex-start;
                                    margin-bottom: 8px;
                                ">
                                    <h4 style="margin: 0; color: #374151; font-size: 16px;">${prompt.title}</h4>
                                    <span style="
                                        background: #e5e7eb;
                                        color: #374151;
                                        padding: 2px 8px;
                                        border-radius: 12px;
                                        font-size: 12px;
                                        white-space: nowrap;
                                        margin-left: 12px;
                                    ">${prompt.category}</span>
                                </div>
                                <div style="
                                    font-size: 13px;
                                    color: #6b7280;
                                    margin-bottom: 8px;
                                ">
                                    Used ${prompt.used_count || 0} times
                                    ${prompt.updated_at ? `• Last used ${new Date(prompt.updated_at).toLocaleDateString()}` : ''}
                                </div>
                                <div style="
                                    font-size: 13px;
                                    color: #9ca3af;
                                    line-height: 1.4;
                                    max-height: 2.8em;
                                    overflow: hidden;
                                ">${prompt.content ? prompt.content.substring(0, 120) + (prompt.content.length > 120 ? '...' : '') : ''}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="
                        padding: 20px 30px;
                        border-top: 1px solid #e5e7eb;
                        background: #f9fafb;
                        text-align: center;
                        font-size: 13px;
                        color: #6b7280;
                    ">
                        💡 Click on any prompt to copy it to clipboard
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Add event listeners
        dialog.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelectorAll('.recent-prompt-item').forEach(item => {
            item.addEventListener('click', async () => {
                const promptId = item.dataset.promptId;
                try {
                    const content = await this.getPromptContent(promptId);
                    await navigator.clipboard.writeText(content);
                    this.showNotification('✅ Prompt copied to clipboard', 'success');
                    
                    // Record usage
                    chrome.runtime.sendMessage({
                        action: 'usePrompt',
                        promptId: promptId
                    });
                    
                    document.body.removeChild(dialog);
                } catch (error) {
                    console.error('Failed to copy prompt:', error);
                    this.showNotification('Failed to copy prompt', 'error');
                }
            });
        });
    }

    // Handle using a specific prompt
    async handleUsePrompt(promptId) {
        const activeElement = document.activeElement;
        if (this.isRelevantTextField(activeElement)) {
            await this.usePrompt(promptId, activeElement);
        } else {
            try {
                const content = await this.getPromptContent(promptId);
                await navigator.clipboard.writeText(content);
                this.showNotification('✅ Prompt copied to clipboard (no active text field)', 'success');
            } catch (error) {
                console.error('Failed to copy prompt:', error);
                this.showNotification('Failed to use prompt', 'error');
            }
        }
    }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const extension = window.promptManagerExtension;
    if (!extension) return;

    switch (request.action) {
        case 'showPromptSuggestions':
            extension.handleContextMenuSuggestions(request.selectedText);
            break;
        case 'saveAsPromptTemplate':
            extension.handleSaveAsTemplate(request.selectedText);
            break;
        case 'showRecentPrompts':
            extension.handleShowRecentPrompts();
            break;
        case 'usePrompt':
            extension.handleUsePrompt(request.promptId);
            break;
    }
});

// Initialize the extension
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.promptManagerExtension = new PromptManagerExtension();
    });
} else {
    window.promptManagerExtension = new PromptManagerExtension();
}