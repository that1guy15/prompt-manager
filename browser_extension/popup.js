// Popup script for Prompt Manager Extension
class PopupManager {
    constructor() {
        this.apiUrl = 'http://localhost:5000/api';
        this.init();
    }

    async init() {
        // Load settings
        const settings = await chrome.storage.sync.get(['apiUrl']);
        this.apiUrl = settings.apiUrl || this.apiUrl;

        // Setup event listeners
        this.setupEventListeners();
        
        // Load data
        await this.loadPromptData();
    }

    setupEventListeners() {
        document.getElementById('search-btn').addEventListener('click', () => {
            this.openSearchTab();
        });

        document.getElementById('settings-btn').addEventListener('click', () => {
            chrome.runtime.openOptionsPage();
        });

        document.getElementById('start-setup-btn')?.addEventListener('click', () => {
            this.showServerConfigDialog();
        });

        document.getElementById('server-config-btn')?.addEventListener('click', () => {
            this.showServerConfigDialog();
        });

        document.getElementById('task-master-btn')?.addEventListener('click', () => {
            this.showTaskMasterProjects();
        });

        document.getElementById('help-btn')?.addEventListener('click', () => {
            this.showHelpDialog();
        });
    }

    async loadPromptData() {
        try {
            // Test API connection
            await this.testApiConnection();
            
            // Load prompts
            const prompts = await this.fetchPrompts();
            
            // Update UI
            this.updateStats(prompts);
            this.displayRecentPrompts(prompts);
            this.showMainContent();
            
        } catch (error) {
            console.error('Failed to load prompt data:', error);
            
            // Check if this is a first-time setup
            const settings = await chrome.storage.sync.get(['hasCompletedSetup']);
            if (!settings.hasCompletedSetup) {
                this.showSetupRequired();
            } else {
                this.showError('Failed to connect to Prompt Manager API. Click "Server Config" to reconfigure.');
            }
        }
    }

    showSetupRequired() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('status').style.display = 'none';
        document.getElementById('setup-required').style.display = 'block';
    }

    async testApiConnection() {
        const response = await fetch(`${this.apiUrl}/prompts?limit=1`);
        if (!response.ok) {
            throw new Error(`API connection failed: ${response.statusText}`);
        }
        
        // Update status
        const statusEl = document.getElementById('status');
        statusEl.className = 'status connected';
        statusEl.innerHTML = '<div class="status-dot"></div><span>Connected to API</span>';
    }

    async fetchPrompts() {
        const response = await fetch(`${this.apiUrl}/prompts`);
        if (!response.ok) {
            throw new Error(`Failed to fetch prompts: ${response.statusText}`);
        }
        return await response.json();
    }

    updateStats(prompts) {
        const totalPromptsEl = document.getElementById('total-prompts');
        const usedTodayEl = document.getElementById('used-today');

        totalPromptsEl.textContent = prompts.length;
        
        // Calculate more meaningful usage stats
        const today = new Date().toDateString();
        const usedToday = prompts.filter(prompt => {
            if (prompt.last_used) {
                const lastUsedDate = new Date(prompt.last_used).toDateString();
                return lastUsedDate === today;
            }
            return false;
        }).length;
        
        usedTodayEl.textContent = usedToday;
    }

    displayRecentPrompts(prompts) {
        const container = document.getElementById('recent-prompts-list');
        
        // Sort by usage count and last used, take top 5
        const topPrompts = prompts
            .sort((a, b) => {
                // Primary sort by usage count
                const usageDiff = (b.used_count || 0) - (a.used_count || 0);
                if (usageDiff !== 0) return usageDiff;
                
                // Secondary sort by last used
                const aLastUsed = a.last_used ? new Date(a.last_used) : new Date(0);
                const bLastUsed = b.last_used ? new Date(b.last_used) : new Date(0);
                return bLastUsed - aLastUsed;
            })
            .slice(0, 5);

        if (topPrompts.length === 0) {
            container.innerHTML = `
                <div style="padding: 24px; text-align: center; color: #6c757d;">
                    <div style="font-size: 32px; margin-bottom: 12px;">📝</div>
                    <div style="font-weight: 500; margin-bottom: 8px;">No prompts found</div>
                    <div style="font-size: 12px;">Create your first prompt template using the context menu</div>
                </div>
            `;
            return;
        }

        container.innerHTML = topPrompts.map(prompt => {
            const lastUsed = prompt.last_used ? 
                this.formatRelativeTime(new Date(prompt.last_used)) : 
                'Never used';
            
            const usageCount = prompt.used_count || 0;
            const efficiency = this.calculateEfficiencyScore(prompt);
            
            return `
                <div class="prompt-item" data-prompt-id="${prompt.id}" title="Click to copy to clipboard">
                    <div class="prompt-title">${prompt.title}</div>
                    <div class="prompt-meta">
                        <span class="category-badge">${prompt.category}</span>
                        <span class="usage-info">Used ${usageCount}x</span>
                        ${efficiency > 70 ? '<span class="efficiency-badge high">🔥 Hot</span>' : ''}
                        ${efficiency > 40 && efficiency <= 70 ? '<span class="efficiency-badge medium">⚡ Active</span>' : ''}
                    </div>
                    <div class="prompt-stats">
                        <span class="last-used">${lastUsed}</span>
                        ${prompt.tags && prompt.tags.length > 0 ? 
                            `<span class="tags">${prompt.tags.slice(0, 2).join(', ')}</span>` : ''
                        }
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers with enhanced feedback
        container.querySelectorAll('.prompt-item').forEach(item => {
            item.addEventListener('click', async () => {
                const promptId = item.dataset.promptId;
                const promptTitle = item.querySelector('.prompt-title').textContent;
                
                try {
                    await this.usePrompt(promptId);
                    this.showSuccessNotification(`✅ "${promptTitle}" copied to clipboard`);
                    this.recordPromptUsage(promptId);
                } catch (error) {
                    console.error('Failed to use prompt:', error);
                    this.showErrorNotification('Failed to copy prompt');
                }
            });
        });
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    calculateEfficiencyScore(prompt) {
        const usageCount = prompt.used_count || 0;
        const lastUsed = prompt.last_used ? new Date(prompt.last_used) : null;
        const created = prompt.created_at ? new Date(prompt.created_at) : null;
        
        if (!lastUsed || !created || usageCount === 0) return 0;
        
        const daysSinceCreated = Math.max(1, (Date.now() - created) / (1000 * 60 * 60 * 24));
        const daysSinceLastUsed = (Date.now() - lastUsed) / (1000 * 60 * 60 * 24);
        
        // Recent usage boosts score
        const recencyScore = Math.max(0, 100 - (daysSinceLastUsed * 10));
        // Usage frequency
        const frequencyScore = Math.min(100, (usageCount / daysSinceCreated) * 20);
        
        return Math.round((recencyScore + frequencyScore) / 2);
    }

    async recordPromptUsage(promptId) {
        try {
            await fetch(`${this.apiUrl}/prompts/${promptId}/use`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Failed to record prompt usage:', error);
        }
    }

    showSuccessNotification(message) {
        this.showNotification(message, 'success', '✅');
    }

    showErrorNotification(message) {
        this.showNotification(message, 'error', '❌');
    }

    showNotification(message, type = 'info', icon = '💡') {
        // Remove existing notifications
        document.querySelectorAll('.prompt-notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `prompt-notification ${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${icon}</span>
            <span class="notification-text">${message}</span>
        `;
        
        const styles = {
            position: 'fixed',
            top: '20px',
            right: '20px',
            zIndex: '10000',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            maxWidth: '300px',
            animation: 'slideIn 0.3s ease'
        };
        
        const typeStyles = {
            success: { background: '#dcfce7', color: '#166534', border: '1px solid #bbf7d0' },
            error: { background: '#fee2e2', color: '#991b1b', border: '1px solid #fecaca' },
            info: { background: '#dbeafe', color: '#1e40af', border: '1px solid #bfdbfe' }
        };
        
        Object.assign(notification.style, styles, typeStyles[type]);
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        document.body.removeChild(notification);
                    }
                }, 300);
            }
        }, 3000);
    }

    showServerConfigDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'server-config-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
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
                    max-width: 500px;
                    width: 90%;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                ">
                    <h2 style="margin: 0 0 20px 0; color: #333; display: flex; align-items: center; gap: 10px;">
                        🔧 Server Configuration
                    </h2>
                    
                    <div class="config-section">
                        <h3 style="margin: 0 0 10px 0; color: #555;">Option 1: Start Local Server</h3>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                            <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">
                                Run this command in your Prompt Manager directory:
                            </p>
                            <div style="
                                background: #1a1a1a;
                                color: #00ff00;
                                padding: 10px;
                                border-radius: 6px;
                                font-family: monospace;
                                font-size: 13px;
                                margin-bottom: 10px;
                            ">python3 src/prompt_api.py</div>
                            <p style="margin: 0; color: #666; font-size: 13px;">
                                Server will start on http://localhost:5000
                            </p>
                        </div>
                    </div>

                    <div class="config-section">
                        <h3 style="margin: 0 0 10px 0; color: #555;">Option 2: Custom Server URL</h3>
                        <form class="server-config-form">
                            <input 
                                type="url" 
                                name="serverUrl"
                                placeholder="http://localhost:5000/api"
                                value="${this.apiUrl}"
                                style="
                                    width: 100%;
                                    padding: 12px;
                                    border: 2px solid #e1e5e9;
                                    border-radius: 6px;
                                    font-size: 14px;
                                    margin-bottom: 15px;
                                    box-sizing: border-box;
                                "
                            >
                            <div class="button-group" style="display: flex; gap: 10px;">
                                <button type="button" class="test-connection-btn" style="
                                    flex: 1;
                                    background: #3b82f6;
                                    color: white;
                                    border: none;
                                    padding: 12px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 14px;
                                    font-weight: 500;
                                ">Test Connection</button>
                                <button type="submit" class="save-btn" style="
                                    flex: 1;
                                    background: #10b981;
                                    color: white;
                                    border: none;
                                    padding: 12px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 14px;
                                    font-weight: 500;
                                ">Save & Connect</button>
                            </div>
                            <div class="connection-status" style="
                                margin-top: 15px;
                                padding: 10px;
                                border-radius: 6px;
                                font-size: 14px;
                                text-align: center;
                                display: none;
                            "></div>
                        </form>
                    </div>

                    <div style="margin-top: 20px; text-align: right;">
                        <button class="close-btn" style="
                            background: #6b7280;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                        ">Close</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        const form = dialog.querySelector('.server-config-form');
        const input = form.querySelector('input[name="serverUrl"]');
        const testBtn = dialog.querySelector('.test-connection-btn');
        const saveBtn = dialog.querySelector('.save-btn');
        const closeBtn = dialog.querySelector('.close-btn');
        const statusDiv = dialog.querySelector('.connection-status');

        // Test connection
        testBtn.addEventListener('click', async () => {
            const url = input.value.trim();
            if (!url) return;

            testBtn.textContent = '🔍 Testing...';
            testBtn.disabled = true;
            statusDiv.style.display = 'block';
            statusDiv.textContent = 'Testing connection...';
            statusDiv.style.background = '#dbeafe';
            statusDiv.style.color = '#1e40af';

            try {
                const healthUrl = url.replace('/api', '').replace(/\/$/, '') + '/health';
                const response = await fetch(healthUrl, { 
                    method: 'GET',
                    signal: AbortSignal.timeout(5000)
                });
                
                if (response.ok) {
                    statusDiv.textContent = '✅ Connection successful!';
                    statusDiv.style.background = '#dcfce7';
                    statusDiv.style.color = '#166534';
                } else {
                    statusDiv.textContent = '❌ Server responded with error';
                    statusDiv.style.background = '#fee2e2';
                    statusDiv.style.color = '#991b1b';
                }
            } catch (error) {
                statusDiv.textContent = '❌ Connection failed - make sure server is running';
                statusDiv.style.background = '#fee2e2';
                statusDiv.style.color = '#991b1b';
            } finally {
                testBtn.textContent = 'Test Connection';
                testBtn.disabled = false;
            }
        });

        // Save configuration
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = input.value.trim();
            
            if (!url) {
                statusDiv.style.display = 'block';
                statusDiv.textContent = 'Please enter a server URL';
                statusDiv.style.background = '#fee2e2';
                statusDiv.style.color = '#991b1b';
                return;
            }

            try {
                this.apiUrl = url;
                await chrome.storage.sync.set({ 
                    apiUrl: url,
                    hasCompletedSetup: true
                });
                
                statusDiv.style.display = 'block';
                statusDiv.textContent = '✅ Configuration saved! Refreshing...';
                statusDiv.style.background = '#dcfce7';
                statusDiv.style.color = '#166534';
                
                setTimeout(() => {
                    document.body.removeChild(dialog);
                    window.location.reload();
                }, 1500);
                
            } catch (error) {
                statusDiv.style.display = 'block';
                statusDiv.textContent = '❌ Failed to save configuration';
                statusDiv.style.background = '#fee2e2';
                statusDiv.style.color = '#991b1b';
            }
        });

        closeBtn.addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        input.focus();
        input.select();
    }

    async showTaskMasterProjects() {
        try {
            const response = await fetch(`${this.apiUrl}/projects`);
            if (!response.ok) {
                throw new Error('Failed to fetch projects');
            }
            
            const projects = await response.json();
            this.displayTaskMasterProjects(projects);
            
        } catch (error) {
            console.error('Failed to fetch Task-Master projects:', error);
            this.showErrorNotification('Failed to load Task-Master projects. Make sure server is running.');
        }
    }

    displayTaskMasterProjects(projects) {
        const dialog = document.createElement('div');
        dialog.className = 'task-master-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
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
                        background: #f8f9fa;
                    ">
                        <h2 style="margin: 0; color: #333; display: flex; align-items: center; gap: 10px;">
                            📋 Task-Master Projects
                        </h2>
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
                        ${projects.length === 0 ? `
                            <div style="padding: 40px; text-align: center; color: #6b7280;">
                                <div style="font-size: 48px; margin-bottom: 16px;">📂</div>
                                <p>No Task-Master projects found</p>
                                <p style="font-size: 13px;">Make sure Task-Master integration is set up</p>
                            </div>
                        ` : projects.map(project => `
                            <div class="project-item" data-project-id="${project.id}" style="
                                padding: 20px 30px;
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
                                    <h4 style="margin: 0; color: #374151; font-size: 16px;">${project.name}</h4>
                                    <span style="
                                        background: ${project.active ? '#dcfce7' : '#f3f4f6'};
                                        color: ${project.active ? '#166534' : '#6b7280'};
                                        padding: 2px 8px;
                                        border-radius: 12px;
                                        font-size: 12px;
                                        white-space: nowrap;
                                        margin-left: 12px;
                                    ">${project.active ? '🟢 Active' : '⚫ Inactive'}</span>
                                </div>
                                <div style="
                                    font-size: 13px;
                                    color: #6b7280;
                                    margin-bottom: 8px;
                                    font-family: monospace;
                                ">${project.path}</div>
                                <div style="
                                    font-size: 13px;
                                    color: #9ca3af;
                                    line-height: 1.4;
                                ">
                                    ${project.task_count || 0} tasks • 
                                    Branch: ${project.git_info?.branch || 'unknown'} • 
                                    ${project.git_info?.commits_ahead || 0} commits ahead
                                </div>
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
                        💡 Click on a project to view tasks and get context-aware prompts
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Add event listeners
        dialog.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', async () => {
                const projectId = item.dataset.projectId;
                await this.showProjectDetails(projectId);
                document.body.removeChild(dialog);
            });
        });
    }

    async showProjectDetails(projectId) {
        try {
            const response = await fetch(`${this.apiUrl}/projects/${projectId}/context`);
            if (!response.ok) {
                throw new Error('Failed to fetch project details');
            }
            
            const projectContext = await response.json();
            this.displayProjectDetails(projectContext);
            
        } catch (error) {
            console.error('Failed to fetch project details:', error);
            this.showErrorNotification('Failed to load project details');
        }
    }

    displayProjectDetails(context) {
        const dialog = document.createElement('div');
        dialog.className = 'project-details-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 10004;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    background: white;
                    padding: 0;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    max-width: 800px;
                    width: 95%;
                    max-height: 85vh;
                    overflow: hidden;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                ">
                    <div style="
                        padding: 20px 30px;
                        border-bottom: 1px solid #e5e7eb;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        background: #f8f9fa;
                    ">
                        <h2 style="margin: 0; color: #333; display: flex; align-items: center; gap: 10px;">
                            📋 ${context.project_name}
                        </h2>
                        <button class="close-btn" style="
                            background: none;
                            border: none;
                            font-size: 24px;
                            cursor: pointer;
                            color: #6b7280;
                        ">&times;</button>
                    </div>
                    
                    <div style="padding: 20px 30px; max-height: 500px; overflow-y: auto;">
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">Project Overview</h3>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 13px;">
                                <div style="margin-bottom: 8px;"><strong>Path:</strong> ${context.project_path}</div>
                                <div style="margin-bottom: 8px;"><strong>Branch:</strong> ${context.git_branch}</div>
                                <div style="margin-bottom: 8px;"><strong>Status:</strong> ${context.git_status}</div>
                                <div><strong>Tasks:</strong> ${context.active_tasks?.length || 0} active</div>
                            </div>
                        </div>

                        ${context.active_tasks && context.active_tasks.length > 0 ? `
                            <div style="margin-bottom: 20px;">
                                <h3 style="margin: 0 0 10px 0; color: #374151;">Active Tasks</h3>
                                <div style="max-height: 200px; overflow-y: auto;">
                                    ${context.active_tasks.map(task => `
                                        <div style="
                                            background: white;
                                            border: 1px solid #e5e7eb;
                                            border-radius: 6px;
                                            padding: 12px;
                                            margin-bottom: 8px;
                                        ">
                                            <div style="
                                                display: flex;
                                                justify-content: space-between;
                                                align-items: flex-start;
                                                margin-bottom: 6px;
                                            ">
                                                <strong style="color: #374151;">${task.title}</strong>
                                                <span style="
                                                    background: ${task.priority === 'high' ? '#fee2e2' : task.priority === 'medium' ? '#fef3c7' : '#f0f9ff'};
                                                    color: ${task.priority === 'high' ? '#991b1b' : task.priority === 'medium' ? '#92400e' : '#1e40af'};
                                                    padding: 2px 6px;
                                                    border-radius: 4px;
                                                    font-size: 11px;
                                                ">${task.priority}</span>
                                            </div>
                                            ${task.description ? `<div style="font-size: 13px; color: #6b7280; margin-bottom: 6px;">${task.description}</div>` : ''}
                                            <div style="font-size: 12px; color: #9ca3af;">
                                                Status: ${task.status} • Created: ${task.created_date}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}

                        ${context.recent_commits && context.recent_commits.length > 0 ? `
                            <div style="margin-bottom: 20px;">
                                <h3 style="margin: 0 0 10px 0; color: #374151;">Recent Commits</h3>
                                <div style="max-height: 150px; overflow-y: auto;">
                                    ${context.recent_commits.slice(0, 5).map(commit => `
                                        <div style="
                                            padding: 8px 12px;
                                            border-left: 3px solid #e5e7eb;
                                            margin-bottom: 8px;
                                            font-size: 13px;
                                        ">
                                            <div style="font-family: monospace; color: #374151; margin-bottom: 4px;">
                                                ${commit.hash.substring(0, 8)}
                                            </div>
                                            <div style="color: #6b7280;">${commit.message}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <div style="
                        padding: 20px 30px;
                        border-top: 1px solid #e5e7eb;
                        background: #f9fafb;
                        display: flex;
                        gap: 12px;
                        justify-content: center;
                    ">
                        <button class="use-taskmaster-prompt-btn" style="
                            background: #3b82f6;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            font-weight: 500;
                        ">🧠 Generate Task-Master Prompt</button>
                        <button class="copy-context-btn" style="
                            background: #10b981;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            font-weight: 500;
                        ">📋 Copy Project Context</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Event listeners
        dialog.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelector('.use-taskmaster-prompt-btn').addEventListener('click', async () => {
            try {
                const response = await fetch(`${this.apiUrl}/prompts/4/render`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ variables: context.variables })
                });
                
                const result = await response.json();
                await navigator.clipboard.writeText(result.content);
                this.showSuccessNotification('✅ Task-Master prompt copied to clipboard!');
                document.body.removeChild(dialog);
                
            } catch (error) {
                console.error('Failed to generate Task-Master prompt:', error);
                this.showErrorNotification('Failed to generate Task-Master prompt');
            }
        });

        dialog.querySelector('.copy-context-btn').addEventListener('click', async () => {
            const contextText = JSON.stringify(context, null, 2);
            await navigator.clipboard.writeText(contextText);
            this.showSuccessNotification('✅ Project context copied to clipboard!');
        });
    }

    showHelpDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'help-dialog';
        dialog.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
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
                    max-width: 600px;
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
                        background: #f8f9fa;
                    ">
                        <h2 style="margin: 0; color: #333; display: flex; align-items: center; gap: 10px;">
                            ❓ How to Use Prompt Manager
                        </h2>
                        <button class="close-btn" style="
                            background: none;
                            border: none;
                            font-size: 24px;
                            cursor: pointer;
                            color: #6b7280;
                        ">&times;</button>
                    </div>
                    
                    <div style="padding: 20px 30px; max-height: 400px; overflow-y: auto;">
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">🚀 Getting Started</h3>
                            <ol style="margin: 0; padding-left: 20px; color: #6b7280; line-height: 1.6;">
                                <li><strong>Start the Backend:</strong> Run <code>python3 src/prompt_api.py</code> in your terminal</li>
                                <li><strong>Configure Server:</strong> Click "Server Config" to set your API URL</li>
                                <li><strong>Start Using:</strong> Right-click on any webpage to access prompt features</li>
                            </ol>
                        </div>

                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">🎯 Key Features</h3>
                            <ul style="margin: 0; padding-left: 20px; color: #6b7280; line-height: 1.6;">
                                <li><strong>Smart Suggestions:</strong> Get AI-powered prompt recommendations based on context</li>
                                <li><strong>Template Library:</strong> Save and reuse your best prompts</li>
                                <li><strong>Task-Master Integration:</strong> Generate prompts with full project context</li>
                                <li><strong>Right-Click Access:</strong> Quick access from any text field</li>
                            </ul>
                        </div>

                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">⌨️ Keyboard Shortcuts</h3>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                                <div style="margin-bottom: 8px;"><code>Ctrl+Shift+P</code> - Toggle prompt widget</div>
                                <div><code>Right-click</code> - Access all prompt features</div>
                            </div>
                        </div>

                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; color: #374151;">🔧 Troubleshooting</h3>
                            <ul style="margin: 0; padding-left: 20px; color: #6b7280; line-height: 1.6;">
                                <li><strong>Connection Failed:</strong> Make sure the backend server is running</li>
                                <li><strong>No Prompts:</strong> Create your first prompt using "Save as Template"</li>
                                <li><strong>Task-Master Issues:</strong> Ensure Task-Master integration is configured</li>
                            </ul>
                        </div>
                    </div>

                    <div style="
                        padding: 20px 30px;
                        border-top: 1px solid #e5e7eb;
                        background: #f9fafb;
                        text-align: center;
                        font-size: 13px;
                        color: #6b7280;
                    ">
                        Need more help? Check the documentation or open an issue on GitHub
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        dialog.querySelector('.close-btn').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });
    }

    async usePrompt(promptId) {
        try {
            // Get the active tab
            const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            // Send message to content script to use the prompt
            await chrome.tabs.sendMessage(activeTab.id, {
                action: 'usePrompt',
                promptId: promptId
            });
            
            // Close popup
            window.close();
            
        } catch (error) {
            console.error('Failed to use prompt:', error);
            this.showError('Failed to use prompt. Make sure you\'re on a supported page.');
        }
    }

    openSearchTab() {
        chrome.tabs.create({
            url: chrome.runtime.getURL('search.html')
        });
    }

    showMainContent() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
    }

    showError(message) {
        document.getElementById('loading').style.display = 'none';
        const errorEl = document.getElementById('error-message');
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        
        const statusEl = document.getElementById('status');
        statusEl.className = 'status disconnected';
        statusEl.innerHTML = '<div class="status-dot"></div><span>Connection failed</span>';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PopupManager();
});