# Project Management Guide

## Overview

The Prompt Manager now provides comprehensive control over which Task-Master projects are available and how they're managed, giving users full control over their project registry.

## 🎛️ **Manual Project Management**

### CLI Commands

#### **Add Projects Manually**
```bash
# Add a project with auto-detection of Task-Master directory
python3 src/project_registry.py add "My Project" /path/to/project

# Add with specific Task-Master directory
python3 src/project_registry.py add "My Project" /path/to/project --task-master-dir /path/to/project/.taskmaster

# Examples
python3 src/project_registry.py add "Auth System" ~/projects/auth-system
python3 src/project_registry.py add "E-commerce" ~/work/ecommerce-platform --task-master-dir ~/work/ecommerce-platform/tasks
```

#### **List and Filter Projects**
```bash
# List all enabled projects (default)
python3 src/project_registry.py list

# List all projects including disabled ones
python3 src/project_registry.py list --all

# List only active projects (recent activity)
python3 src/project_registry.py list --active
```

#### **Enable/Disable Projects**
```bash
# Disable a project (hide from selections but keep in registry)
python3 src/project_registry.py disable a1b2c3d4

# Re-enable a project
python3 src/project_registry.py enable a1b2c3d4

# Remove project completely
python3 src/project_registry.py remove a1b2c3d4
```

#### **Update Project Information**
```bash
# Update project name
python3 src/project_registry.py update a1b2c3d4 --name "New Project Name"

# Update project path
python3 src/project_registry.py update a1b2c3d4 --path /new/path/to/project

# Update Task-Master directory
python3 src/project_registry.py update a1b2c3d4 --task-master-dir /new/task/master/dir
```

#### **Settings Management**
```bash
# Show current settings
python3 src/project_registry.py settings --show

# Disable auto-discovery
python3 src/project_registry.py settings --auto-discovery off

# Enable auto-discovery
python3 src/project_registry.py settings --auto-discovery on
```

### Example Output
```bash
$ python3 src/project_registry.py list --all

📋 Projects (including disabled) (4):
👉 🟢 file-processing-redesign [a1b2c3d4] [MANUAL]
      /Users/you/workspace/file-processing-redesign
      Task-Master: /Users/you/workspace/file-processing-redesign/task-master (12 tasks)
      Last used: 2025-01-24T10:30:00Z
      Git: feature/unified-processing

   ⚫ old-project [e5f6g7h8] [DISABLED]
      /Users/you/old-projects/legacy-system
      Task-Master: /Users/you/old-projects/legacy-system/tasks (3 tasks)

   🟢 dashboard-v2 [i9j0k1l2]
      /Users/you/work/dashboard-v2
      Task-Master: /Users/you/work/dashboard-v2/.taskmaster (8 tasks)
      Git: feature/charts

   🟢 api-gateway [m3n4o5p6] [MANUAL]
      /Users/you/microservices/api-gateway
      Task-Master: /Users/you/microservices/api-gateway/task-master (5 tasks)
      Last used: 2025-01-23T14:20:00Z
      Git: main
```

## 🌐 **Browser Extension Project Management**

### Settings Page Access
1. **Right-click extension icon** → "Options"
2. **Or visit**: `chrome-extension://[extension-id]/options.html`

### Project Management Features

#### **Visual Project List**
- **Enable/Disable Toggle**: Control project visibility
- **Refresh Button**: Update project information
- **Remove Button**: Delete projects from registry
- **Status Indicators**: Show active/inactive and manual/discovered projects

#### **Add Projects Manually**
1. Click **"Add Manually"** button
2. Enter **Project Name** and **Project Path**
3. Optionally specify **Task-Master Directory**
4. Click **"Add Project"**

#### **Auto-Discovery**
- **"Discover New"** button scans common directories
- **Auto-discovery toggle** controls automatic scanning
- **Refresh Projects** updates existing project information

#### **Connection Testing**
- **Test Connection** button verifies API connectivity
- **API URL** configuration for custom setups

## 🎯 **Use Cases and Workflows**

### **Scenario 1: Selective Project Management**
```bash
# You have many projects but only want some available to Prompt Manager

# 1. Disable auto-discovery
python3 src/project_registry.py settings --auto-discovery off

# 2. Manually add only the projects you want
python3 src/project_registry.py add "Current Project" ~/active/current-project
python3 src/project_registry.py add "Client Work" ~/clients/big-client-project

# 3. Your pmcli command now only shows these 2 projects
pmcli --list-projects
```

### **Scenario 2: Team Environment**
```bash
# Team lead sets up standard projects for the team

# Add team projects
python3 src/project_registry.py add "Main Product" /team/main-product
python3 src/project_registry.py add "Client Portal" /team/client-portal
python3 src/project_registry.py add "Mobile App" /team/mobile-app

# Team members get consistent project list
pmcli --list-projects  # Shows all 3 team projects
```

### **Scenario 3: Freelancer with Multiple Clients**
```bash
# Organize by client, enable/disable as needed

python3 src/project_registry.py add "Client A - Website" ~/clients/client-a/website
python3 src/project_registry.py add "Client A - Mobile" ~/clients/client-a/mobile
python3 src/project_registry.py add "Client B - Platform" ~/clients/client-b/platform

# When working on Client A projects, disable Client B
python3 src/project_registry.py disable client-b-id

# Switch focus to Client B later
python3 src/project_registry.py enable client-b-id
python3 src/project_registry.py disable client-a-website-id
python3 src/project_registry.py disable client-a-mobile-id
```

### **Scenario 4: Legacy Project Management**
```bash
# Keep old projects in registry but disabled

# Instead of removing (loses history)
python3 src/project_registry.py remove old-project-id

# Disable to hide from normal use but keep for reference
python3 src/project_registry.py disable old-project-id

# View all projects including disabled when needed
python3 src/project_registry.py list --all
```

## 🔧 **Advanced Configuration**

### **Registry File Location**
- **Default**: `~/.prompt_manager_projects.json`
- **Custom**: Set `PROMPT_MANAGER_REGISTRY` environment variable

### **Project Structure Requirements**
Projects need **one of these** to be detected:
- `task-master/` directory
- `.task-master/` directory  
- `tasks/` directory with `.md` files
- `task-master.yml` configuration file
- `task-master.json` configuration file

### **Manual vs Auto-Discovered Projects**
- **Auto-discovered**: Found by scanning common directories
- **Manual**: Added explicitly by user
- **Indicators**: `[MANUAL]` tag in listings
- **Behavior**: Manual projects are never automatically removed

### **Project States**
- **Enabled**: Shows in normal listings and selections
- **Disabled**: Hidden from normal use but kept in registry
- **Active**: Has recent file modifications (automatically detected)
- **Current**: The project selected for current session

## 🚀 **Browser Extension Integration**

### **Project Selection Flow**
1. **Open Claude.ai** (or supported platform)
2. **Click extension icon** or use **Ctrl+Shift+P**
3. **Click 📂 project button** in popup
4. **Select project** from visual list
5. **Click "Use Task-Master Prompt"** - copies rendered prompt with project context

### **Extension Settings**
- **Enable/Disable Extension**: Master on/off switch
- **Auto-suggest Prompts**: Show suggestions when focusing text fields
- **Show Widget**: Display floating access widget
- **Auto-discovery**: Automatically find new projects

## 📊 **Benefits of Manual Project Management**

### **Control**
- **Choose exactly** which projects appear in selection lists
- **Hide legacy projects** without losing them
- **Organize by client, team, or priority**

### **Performance**
- **Faster selections** with fewer projects in lists
- **Reduced noise** from inactive projects
- **Focused context** for current work

### **Security** 
- **Exclude sensitive** projects from general use
- **Control access** in team environments
- **Separate personal/work** projects

### **Maintenance**
- **Easy cleanup** of old projects
- **Update project information** as structures change
- **Backup registry** for team sharing

## 🔄 **Migration and Backup**

### **Export Project Registry**
```bash
# Registry is stored in JSON format
cp ~/.prompt_manager_projects.json ~/backup/prompt_projects_backup.json
```

### **Import/Restore Registry**
```bash
# Restore from backup
cp ~/backup/prompt_projects_backup.json ~/.prompt_manager_projects.json
```

### **Share Team Configuration**
```bash
# Export team projects
python3 src/project_registry.py list --all > team_projects.txt

# Share registry file (edit to remove personal projects first)
cp ~/.prompt_manager_projects.json team_shared_registry.json
```

This comprehensive project management system gives users complete control over their Task-Master integration while maintaining the convenience of auto-discovery for those who prefer it.