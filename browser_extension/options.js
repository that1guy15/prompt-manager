// Options page script for Prompt Manager Extension
class OptionsManager {
    constructor() {
        this.apiUrl = 'http://localhost:5000/api';
        this.projects = [];
        this.init();
    }

    async init() {
        await this.loadSettings();
        this.setupEventListeners();
        await this.loadProjects();
    }

    async loadSettings() {
        try {
            const settings = await chrome.storage.sync.get([
                'apiUrl', 'isEnabled', 'autoSuggest', 'showWidget', 'autoDiscovery',
                'aiProvider', 'aiApiKey', 'aiModel'
            ]);

            document.getElementById('api-url').value = settings.apiUrl || this.apiUrl;
            document.getElementById('extension-enabled').checked = settings.isEnabled !== false;
            document.getElementById('auto-suggest').checked = settings.autoSuggest !== false;
            document.getElementById('show-widget').checked = settings.showWidget !== false;
            document.getElementById('auto-discovery').checked = settings.autoDiscovery !== false;

            // Load AI provider settings
            if (settings.aiProvider) {
                document.getElementById('ai-provider').value = settings.aiProvider;
                await this.loadModelsForProvider(settings.aiProvider);
                if (settings.aiModel) {
                    document.getElementById('ai-model').value = settings.aiModel;
                }
            }
            if (settings.aiApiKey) {
                document.getElementById('api-key').value = settings.aiApiKey;
            }

            this.apiUrl = settings.apiUrl || this.apiUrl;
            
            // Also load provider config from backend
            await this.loadProviderConfig();
        } catch (error) {
            this.showStatus('Failed to load settings', 'error');
        }
    }
    
    async loadProviderConfig() {
        try {
            const response = await fetch(`${this.apiUrl}/config`);
            if (response.ok) {
                const config = await response.json();
                if (config.provider && !document.getElementById('ai-provider').value) {
                    document.getElementById('ai-provider').value = config.provider;
                    await this.loadModelsForProvider(config.provider);
                    if (config.model) {
                        document.getElementById('ai-model').value = config.model;
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load provider config:', error);
        }
    }
    
    async loadModelsForProvider(provider) {
        const modelSelect = document.getElementById('ai-model');
        modelSelect.innerHTML = '<option value="">Select a model...</option>';
        
        try {
            const response = await fetch(`${this.apiUrl}/config`);
            if (response.ok) {
                const config = await response.json();
                const providerInfo = config.providers[provider];
                if (providerInfo && providerInfo.models) {
                    providerInfo.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        if (model === providerInfo.default_model) {
                            option.textContent += ' (default)';
                        }
                        modelSelect.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }

    setupEventListeners() {
        // API Configuration
        document.getElementById('test-connection').addEventListener('click', () => {
            this.testConnection();
        });
        
        // AI Provider Configuration
        document.getElementById('ai-provider').addEventListener('change', async (e) => {
            if (e.target.value) {
                await this.loadModelsForProvider(e.target.value);
            }
        });
        
        document.getElementById('validate-api-key').addEventListener('click', () => {
            this.validateApiKey();
        });
        
        document.getElementById('save-provider').addEventListener('click', () => {
            this.saveProviderConfig();
        });

        // Project Management
        document.getElementById('refresh-projects').addEventListener('click', () => {
            this.loadProjects();
        });

        document.getElementById('discover-projects').addEventListener('click', () => {
            this.discoverProjects();
        });

        document.getElementById('add-project-btn').addEventListener('click', () => {
            this.showAddProjectForm();
        });

        document.getElementById('save-project').addEventListener('click', () => {
            this.addProject();
        });

        document.getElementById('cancel-add').addEventListener('click', () => {
            this.hideAddProjectForm();
        });

        // Settings
        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('reset-settings').addEventListener('click', () => {
            this.resetSettings();
        });

        // API URL change
        document.getElementById('api-url').addEventListener('change', (e) => {
            this.apiUrl = e.target.value;
        });

        // Help system handlers
        document.getElementById('quick-start-help').addEventListener('click', () => {
            this.showHelpContent('quick-start');
        });

        document.getElementById('project-help').addEventListener('click', () => {
            this.showHelpContent('project-setup');
        });

        document.getElementById('troubleshooting-help').addEventListener('click', () => {
            this.showHelpContent('troubleshooting');
        });

        document.getElementById('keyboard-shortcuts').addEventListener('click', () => {
            this.showHelpContent('shortcuts');
        });

        // File browser for project path
        document.getElementById('browse-path').addEventListener('click', () => {
            this.browseForPath();
        });
    }

    async testConnection() {
        const button = document.getElementById('test-connection');
        button.textContent = 'Testing...';
        button.disabled = true;

        try {
            // Try health endpoint first (simpler than prompts endpoint)
            const healthUrl = this.apiUrl.replace('/api', '').replace(/\/$/, '') + '/health';
            
            const response = await fetch(healthUrl, {
                method: 'GET',
                mode: 'cors',
                credentials: 'omit',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showStatus(`✅ Connection successful! Server status: ${data.status || 'ok'}`, 'success');
            } else if (response.status === 404) {
                // Try the old endpoint format
                const fallbackResponse = await fetch(`${this.apiUrl}/prompts?limit=1`, {
                    method: 'GET',
                    mode: 'cors',
                    credentials: 'omit',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });
                
                if (fallbackResponse.ok) {
                    this.showStatus('✅ Connection successful!', 'success');
                } else {
                    this.showStatus(`❌ Connection failed: Server responded with ${response.status}`, 'error');
                }
            } else {
                this.showStatus(`❌ Connection failed: ${response.status} ${response.statusText}`, 'error');
            }
        } catch (error) {
            let errorMessage = error.message;
            
            // Provide more helpful error messages
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot reach server. Make sure the API server is running on the specified URL.';
            } else if (error.message.includes('CORS')) {
                errorMessage = 'CORS policy blocked the request. Check server CORS configuration.';
            } else if (error.message.includes('NetworkError')) {
                errorMessage = 'Network error. Check your internet connection and server URL.';
            }
            
            this.showStatus(`❌ Connection failed: ${errorMessage}`, 'error');
        } finally {
            button.textContent = 'Test Connection';
            button.disabled = false;
        }
    }

    async loadProjects() {
        const container = document.getElementById('project-list');
        container.innerHTML = '<div class="loading">Loading projects...</div>';

        try {
            const response = await fetch(`${this.apiUrl}/projects`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.projects = await response.json();
            this.renderProjects();
        } catch (error) {
            container.innerHTML = `
                <div style="text-align: center; color: #ef4444; padding: 20px;">
                    Failed to load projects: ${error.message}
                    <br><br>
                    <button class="btn btn-secondary" onclick="window.location.reload()">Retry</button>
                </div>
            `;
        }
    }

    renderProjects() {
        const container = document.getElementById('project-list');

        if (this.projects.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; color: #6c757d; padding: 20px;">
                    No projects found. Use "Discover New" or "Add Manually" to add projects.
                </div>
            `;
            return;
        }

        container.innerHTML = this.projects.map(project => `
            <div class="project-item" data-project-id="${project.id}">
                <div class="project-info">
                    <div class="project-name">
                        ${project.name}
                        ${project.manually_added ? '<span style="font-size: 12px; color: #3b82f6;">[MANUAL]</span>' : ''}
                        ${!project.enabled ? '<span style="font-size: 12px; color: #ef4444;">[DISABLED]</span>' : ''}
                    </div>
                    <div class="project-path">${project.path}</div>
                    <div style="font-size: 12px; color: #6c757d; margin-top: 4px;">
                        ${project.task_count} tasks • 
                        ${project.active ? '🟢 Active' : '⚫ Inactive'} • 
                        Branch: ${project.git_info?.branch || 'unknown'}
                    </div>
                </div>
                <div class="project-actions">
                    <label class="switch" title="Enable/Disable">
                        <input type="checkbox" ${project.enabled ? 'checked' : ''} 
                               onchange="optionsManager.toggleProject('${project.id}', this.checked)">
                        <span class="slider"></span>
                    </label>
                    <button class="btn btn-secondary" onclick="optionsManager.refreshProject('${project.id}')">
                        Refresh
                    </button>
                    <button class="btn btn-danger" onclick="optionsManager.removeProject('${project.id}', '${project.name}')">
                        Remove
                    </button>
                </div>
            </div>
        `).join('');
    }

    async discoverProjects() {
        const button = document.getElementById('discover-projects');
        button.textContent = 'Discovering...';
        button.disabled = true;

        try {
            const response = await fetch(`${this.apiUrl}/projects/discover`, {
                method: 'POST',
                mode: 'cors',
                credentials: 'omit',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ register: true })
            });

            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('Discovery requires additional permissions. Try adding projects manually instead.');
                } else if (response.status === 404) {
                    throw new Error('Discovery endpoint not found. Make sure you have the latest API server version.');
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const result = await response.json();
            this.showStatus(`✅ Discovered ${result.discovered?.length || 0} projects`, 'success');
            await this.loadProjects();
        } catch (error) {
            let errorMessage = error.message;
            
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot reach discovery service. Make sure the API server is running and accessible.';
            } else if (error.message.includes('CORS')) {
                errorMessage = 'Discovery blocked by security policy. Try adding projects manually.';
            }
            
            this.showStatus(`❌ Discovery failed: ${errorMessage}`, 'error');
        } finally {
            button.textContent = 'Discover New';
            button.disabled = false;
        }
    }

    showAddProjectForm() {
        document.getElementById('add-project-form').classList.remove('hidden');
        document.getElementById('add-project-btn').style.display = 'none';
    }

    hideAddProjectForm() {
        document.getElementById('add-project-form').classList.add('hidden');
        document.getElementById('add-project-btn').style.display = 'inline-block';
        
        // Clear form
        document.getElementById('project-name').value = '';
        document.getElementById('project-path').value = '';
        document.getElementById('task-master-dir').value = '';
    }

    async addProject() {
        const name = document.getElementById('project-name').value.trim();
        const path = document.getElementById('project-path').value.trim();
        const taskMasterDir = document.getElementById('task-master-dir').value.trim() || null;

        if (!name || !path) {
            this.showStatus('❌ Please provide project name and path', 'error');
            return;
        }

        const button = document.getElementById('save-project');
        button.textContent = 'Adding...';
        button.disabled = true;

        try {
            // For browser extension, we need to call the API
            // Since we can't directly call Python functions
            const response = await fetch(`${this.apiUrl}/projects/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    path: path,
                    task_master_dir: taskMasterDir
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            const result = await response.json();
            this.showStatus(`✅ Added project: ${result.name}`, 'success');
            this.hideAddProjectForm();
            await this.loadProjects();
        } catch (error) {
            this.showStatus(`❌ Failed to add project: ${error.message}`, 'error');
        } finally {
            button.textContent = 'Add Project';
            button.disabled = false;
        }
    }

    async toggleProject(projectId, enabled) {
        try {
            const response = await fetch(`${this.apiUrl}/projects/${projectId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const project = this.projects.find(p => p.id === projectId);
            if (project) {
                project.enabled = enabled;
                this.showStatus(`✅ ${enabled ? 'Enabled' : 'Disabled'} project: ${project.name}`, 'success');
            }
        } catch (error) {
            this.showStatus(`❌ Failed to toggle project: ${error.message}`, 'error');
            // Revert checkbox
            const checkbox = document.querySelector(`input[onchange*="${projectId}"]`);
            if (checkbox) {
                checkbox.checked = !enabled;
            }
        }
    }

    async refreshProject(projectId) {
        try {
            const response = await fetch(`${this.apiUrl}/projects/${projectId}/refresh`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.showStatus('✅ Project refreshed', 'success');
            await this.loadProjects();
        } catch (error) {
            this.showStatus(`❌ Failed to refresh project: ${error.message}`, 'error');
        }
    }

    async removeProject(projectId, projectName) {
        if (!confirm(`Are you sure you want to remove "${projectName}"?`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/projects/${projectId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.showStatus(`✅ Removed project: ${projectName}`, 'success');
            await this.loadProjects();
        } catch (error) {
            this.showStatus(`❌ Failed to remove project: ${error.message}`, 'error');
        }
    }

    async saveSettings() {
        const settings = {
            apiUrl: document.getElementById('api-url').value,
            isEnabled: document.getElementById('extension-enabled').checked,
            autoSuggest: document.getElementById('auto-suggest').checked,
            showWidget: document.getElementById('show-widget').checked,
            autoDiscovery: document.getElementById('auto-discovery').checked
        };

        try {
            await chrome.storage.sync.set(settings);
            this.showStatus('✅ Settings saved', 'success');
        } catch (error) {
            this.showStatus('❌ Failed to save settings', 'error');
        }
    }

    async resetSettings() {
        if (!confirm('Are you sure you want to reset all settings to defaults?')) {
            return;
        }

        try {
            await chrome.storage.sync.clear();
            await this.loadSettings();
            this.showStatus('✅ Settings reset to defaults', 'success');
        } catch (error) {
            this.showStatus('❌ Failed to reset settings', 'error');
        }
    }

    showStatus(message, type) {
        const statusEl = document.getElementById('status-message');
        statusEl.textContent = message;
        statusEl.className = `status ${type}`;
        statusEl.classList.remove('hidden');

        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 5000);
    }

    showHelpContent(topic) {
        const helpContent = document.getElementById('help-content');
        const helpSectionContent = document.getElementById('help-section-content');

        const helpTopics = {
            'quick-start': `
                <h3>📚 Quick Start Guide</h3>
                <div style="line-height: 1.6;">
                    <h4>🚀 Get Started in 2 Minutes</h4>
                    <ol>
                        <li><strong>Start API Server:</strong>
                            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0;">python3 src/prompt_api.py</pre>
                        </li>
                        <li><strong>Test Connection:</strong> Click "Test Connection" above ☝️</li>
                        <li><strong>Add a Project:</strong> Use "Add Manually" in the Projects section</li>
                        <li><strong>Visit Claude.ai:</strong> Focus on a text area to see suggestions appear!</li>
                    </ol>
                    
                    <h4>🎯 Quick Actions</h4>
                    <ul>
                        <li><strong>Ctrl+Shift+P</strong> - Quick access popup</li>
                        <li><strong>Click 📂</strong> - Choose Task-Master project</li>
                        <li><strong>Focus text field</strong> - Auto-suggestions appear</li>
                        <li><strong>Right-click extension icon</strong> - Access this settings page</li>
                    </ul>
                    
                    <h4>✨ Supported Websites</h4>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 10px 0;">
                        <span>🔹 Claude.ai</span>
                        <span>🔹 ChatGPT</span>
                        <span>🔹 GitHub</span>
                        <span>🔹 Notion</span>
                        <span>🔹 Linear</span>
                        <span>🔹 Slack</span>
                    </div>
                </div>
            `,
            
            'project-setup': `
                <h3>🔧 Project Setup Guide</h3>
                <div style="line-height: 1.6;">
                    <h4>📂 Adding Projects</h4>
                    <p><strong>Method 1: Browser Extension</strong></p>
                    <ol>
                        <li>Click "Add Manually" button above</li>
                        <li>Enter project name and path</li>
                        <li>Optionally specify Task-Master directory</li>
                        <li>Click "Add Project"</li>
                    </ol>
                    
                    <p><strong>Method 2: Command Line</strong></p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0;">python3 src/project_registry.py add "My Project" /path/to/project</pre>
                    
                    <h4>⚙️ Project Settings</h4>
                    <ul>
                        <li><strong>Enable/Disable:</strong> Toggle projects without deleting them</li>
                        <li><strong>Auto-discovery:</strong> Automatically find new Task-Master projects</li>
                        <li><strong>Refresh:</strong> Update project metadata and discover changes</li>
                    </ul>
                    
                    <h4>🎯 Best Practices</h4>
                    <ul>
                        <li>Use descriptive project names</li>
                        <li>Keep project paths absolute (not relative)</li>
                        <li>Enable auto-discovery for convenience</li>
                        <li>Disable unused projects to reduce clutter</li>
                    </ul>
                </div>
            `,
            
            'troubleshooting': `
                <h3>🆘 Troubleshooting Guide</h3>
                <div style="line-height: 1.6;">
                    <h4>🔗 Connection Issues</h4>
                    <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0;">
                        <strong>Problem:</strong> "Connection failed" or "API server not responding"
                    </div>
                    <ul>
                        <li>Ensure API server is running: <code>python3 src/prompt_api.py</code></li>
                        <li>Check API URL is correct (default: http://localhost:5000/api)</li>
                        <li>Verify no firewall is blocking port 5000</li>
                        <li>Try restarting the API server</li>
                    </ul>
                    
                    <h4>📂 Project Issues</h4>
                    <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0;">
                        <strong>Problem:</strong> "No projects found" or project not showing
                    </div>
                    <ul>
                        <li>Add projects manually using "Add Manually" button</li>
                        <li>Check project paths exist and are accessible</li>
                        <li>Click "Refresh Projects" to update the list</li>
                        <li>Enable "Auto-discovery" setting</li>
                    </ul>
                    
                    <h4>🌐 Browser Extension Issues</h4>
                    <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0;">
                        <strong>Problem:</strong> Extension not working on websites
                    </div>
                    <ul>
                        <li>Check "Enable Extension" is turned on</li>
                        <li>Reload the webpage after changing settings</li>
                        <li>Verify extension permissions in Chrome settings</li>
                        <li>Try disabling and re-enabling the extension</li>
                    </ul>
                    
                    <h4>🔧 Advanced Troubleshooting</h4>
                    <ul>
                        <li><strong>Clear cache:</strong> Right-click extension → "Reload extension"</li>
                        <li><strong>Check console:</strong> F12 → Console tab for error messages</li>
                        <li><strong>Reset settings:</strong> Use "Reset to Defaults" button above</li>
                        <li><strong>Restart browser:</strong> Sometimes needed after major changes</li>
                    </ul>
                </div>
            `,
            
            'shortcuts': `
                <h3>⌨️ Keyboard Shortcuts</h3>
                <div style="line-height: 1.6;">
                    <h4>🚀 Global Shortcuts</h4>
                    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px; margin: 15px 0;">
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; text-align: center;">
                            <code>Ctrl+Shift+P</code>
                        </div>
                        <div>Open quick access popup from any supported website</div>
                        
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; text-align: center;">
                            <code>Escape</code>
                        </div>
                        <div>Close popup or suggestions panel</div>
                        
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; text-align: center;">
                            <code>Tab</code>
                        </div>
                        <div>Navigate through suggestion items</div>
                        
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; text-align: center;">
                            <code>Enter</code>
                        </div>
                        <div>Select highlighted suggestion</div>
                    </div>
                    
                    <h4>📂 Project Selection</h4>
                    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px; margin: 15px 0;">
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; text-align: center;">
                            <code>1-9</code>
                        </div>
                        <div>Quick select project by number in popup</div>
                        
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; text-align: center;">
                            <code>Ctrl+P</code>
                        </div>
                        <div>Toggle project selector when popup is open</div>
                    </div>
                    
                    <h4>💡 Pro Tips</h4>
                    <ul>
                        <li><strong>Quick Access:</strong> Use Ctrl+Shift+P from anywhere for instant prompt access</li>
                        <li><strong>Auto-suggest:</strong> Just focus on a text field - suggestions appear automatically</li>
                        <li><strong>Project Context:</strong> Click 📂 to choose project for context-aware prompts</li>
                        <li><strong>Fast Selection:</strong> Use number keys to quickly select from suggestions</li>
                    </ul>
                    
                    <h4>🎯 Website-Specific Features</h4>
                    <div style="background: #e7f3ff; padding: 10px; border-radius: 4px; margin: 10px 0;">
                        <strong>Claude.ai / ChatGPT:</strong> Suggestions appear in conversation input<br>
                        <strong>GitHub:</strong> Context-aware suggestions in issue/PR descriptions<br>
                        <strong>Notion:</strong> Smart prompts for document creation<br>
                        <strong>Linear:</strong> Issue templates and project context
                    </div>
                </div>
            `
        };

        if (helpTopics[topic]) {
            helpSectionContent.innerHTML = helpTopics[topic];
            helpContent.classList.remove('hidden');
            helpContent.scrollIntoView({ behavior: 'smooth' });
        }
    }

    browseForPath() {
        // Since browser extensions cannot directly access file system,
        // we'll show a helpful dialog with instructions
        const dialog = document.createElement('div');
        dialog.className = 'path-browser-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.7);
                z-index: 10000;
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
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                ">
                    <h3 style="margin: 0 0 15px 0; color: #333; display: flex; align-items: center; gap: 10px;">
                        📁 Find Your Project Path
                    </h3>
                    
                    <div style="margin-bottom: 20px; color: #666; line-height: 1.5;">
                        Browser extensions cannot browse your file system directly. Here's how to find your project path:
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #374151;">🖥️ On macOS/Linux:</h4>
                        <ol style="margin: 0; padding-left: 20px; color: #555;">
                            <li>Open Terminal</li>
                            <li>Navigate to your project: <code>cd /path/to/your/project</code></li>
                            <li>Get full path: <code>pwd</code></li>
                            <li>Copy the output and paste it above</li>
                        </ol>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #374151;">🪟 On Windows:</h4>
                        <ol style="margin: 0; padding-left: 20px; color: #555;">
                            <li>Open File Explorer</li>
                            <li>Navigate to your project folder</li>
                            <li>Click in the address bar</li>
                            <li>Copy the full path and paste it above</li>
                        </ol>
                    </div>
                    
                    <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4 style="margin: 0 0 8px 0; color: #1e40af;">💡 Example paths:</h4>
                        <div style="font-family: monospace; font-size: 13px; color: #374151;">
                            • macOS: <code>/Users/username/projects/my-app</code><br>
                            • Linux: <code>/home/username/projects/my-app</code><br>
                            • Windows: <code>C:\\Users\\username\\projects\\my-app</code>
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <button class="close-dialog-btn" style="
                            background: #3b82f6;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            font-weight: 500;
                        ">Got it!</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);
        
        dialog.querySelector('.close-dialog-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
            // Focus back on the path input
            document.getElementById('project-path').focus();
        });
    }
    
    async validateApiKey() {
        const provider = document.getElementById('ai-provider').value;
        const apiKey = document.getElementById('api-key').value;
        
        if (!provider || !apiKey) {
            this.showProviderStatus('Please select a provider and enter an API key', 'error');
            return;
        }
        
        const button = document.getElementById('validate-api-key');
        button.textContent = 'Validating...';
        button.disabled = true;
        
        try {
            const response = await fetch(`${this.apiUrl}/config/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ provider, api_key: apiKey })
            });
            
            const result = await response.json();
            
            if (result.valid) {
                this.showProviderStatus('✅ API key is valid!', 'success');
            } else {
                this.showProviderStatus(`❌ Invalid API key: ${result.message}`, 'error');
            }
        } catch (error) {
            this.showProviderStatus(`❌ Validation failed: ${error.message}`, 'error');
        } finally {
            button.textContent = 'Validate API Key';
            button.disabled = false;
        }
    }
    
    async saveProviderConfig() {
        const provider = document.getElementById('ai-provider').value;
        const apiKey = document.getElementById('api-key').value;
        const model = document.getElementById('ai-model').value;
        
        if (!provider) {
            this.showProviderStatus('Please select a provider', 'error');
            return;
        }
        
        const button = document.getElementById('save-provider');
        button.textContent = 'Saving...';
        button.disabled = true;
        
        try {
            // Save to browser storage
            await chrome.storage.sync.set({
                aiProvider: provider,
                aiApiKey: apiKey,
                aiModel: model
            });
            
            // Save to backend
            const response = await fetch(`${this.apiUrl}/config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    provider,
                    api_key: apiKey,
                    model
                })
            });
            
            if (response.ok) {
                this.showProviderStatus('✅ Configuration saved successfully!', 'success');
            } else {
                const error = await response.json();
                this.showProviderStatus(`❌ Failed to save: ${error.error}`, 'error');
            }
        } catch (error) {
            this.showProviderStatus(`❌ Save failed: ${error.message}`, 'error');
        } finally {
            button.textContent = 'Save Configuration';
            button.disabled = false;
        }
    }
    
    showProviderStatus(message, type) {
        const statusEl = document.getElementById('provider-status');
        statusEl.textContent = message;
        statusEl.className = `status ${type}`;
        statusEl.classList.remove('hidden');
        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 5000);
    }
}

// Initialize when DOM is loaded
let optionsManager;
document.addEventListener('DOMContentLoaded', () => {
    optionsManager = new OptionsManager();
    
    // Add CSS for help content styling
    const helpStyles = document.createElement('style');
    helpStyles.textContent = `
        .help-content {
            background: #f8f9fa;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .help-content h3 {
            margin-top: 0;
            color: #1a1a1a;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 10px;
        }
        
        .help-content h4 {
            color: #374151;
            margin-top: 25px;
            margin-bottom: 10px;
        }
        
        .help-content code {
            background: #e1e5e9;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
        }
        
        .help-content pre {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            overflow-x: auto;
        }
        
        .help-content ul, .help-content ol {
            padding-left: 20px;
        }
        
        .help-content li {
            margin-bottom: 5px;
        }
    `;
    document.head.appendChild(helpStyles);
});