# Multi-Project Task-Master Integration Guide

## Problem Solved

**Challenge**: Users have multiple Task-Master projects across their computer, and the system needs to know which project context to use for prompt generation.

**Solution**: A comprehensive project registry system that:
- **Auto-discovers** Task-Master projects across your system
- **Remembers** project contexts and usage patterns  
- **Smart detection** based on current working directory
- **Browser integration** with project selection UI

## 🔧 **CLI Usage**

### Initial Setup
```bash
# Discover all Task-Master projects on your system
pmcli --list-projects

# First time: auto-discovers and registers projects
# Output:
📋 Available projects (3):
👉 🟢 1. file-processing-redesign [a1b2c3d4]
      /Users/you/workspace/file-processing-redesign
   ⚫ 2. auth-system [e5f6g7h8]  
      /Users/you/projects/auth-system
   🟢 3. dashboard-v2 [i9j0k1l2]
      /Users/you/work/dashboard-v2
```

### Project Selection

#### Auto-Detection (Recommended)
```bash
# From any project directory
cd /Users/you/workspace/file-processing-redesign
pmcli

# Output:
🔍 Auto-detecting current project...
📂 Found project: file-processing-redesign
💡 Rendering prompt 4...
✅ Generated prompt: Task Master Project Continuation  
📋 Copied to clipboard!

💡 Project: file-processing-redesign
   📂 Active Task: implement-unified-file-manager.md
   🌿 Branch: feature/unified-processing
   📄 PRD: /app/uploads/redesign_v3/PRD_TASK_MASTER.md

🚀 Ready to paste into Claude Code!
```

#### Manual Selection
```bash
# Interactive project selection
pmcli --select-project

# Output:
📋 Select a project:
🟢 1. file-processing-redesign
    /Users/you/workspace/file-processing-redesign
⚫ 2. auth-system
    /Users/you/projects/auth-system

Enter project number: 1
✅ Selected: file-processing-redesign
```

#### Direct Project ID
```bash
# Use specific project
pmcli --project-id a1b2c3d4
```

### Advanced CLI Commands
```bash
# List all projects with details
pmcli --list-projects

# Show extracted context for debugging
pmcli --show-context

# Use different prompt with project context
pmcli --prompt-id 2 --project-id a1b2c3d4

# Registry management
python3 src/project_registry.py discover --register
python3 src/project_registry.py current a1b2c3d4
python3 src/project_registry.py auto
```

## 🌐 **Browser Extension Usage**

### Project Selection in Browser

1. **Click the extension icon** or use **Ctrl+Shift+P**
2. **Click the 📂 project button** in the prompt access popup
3. **Select your Task-Master project** from the list:

```
┌─── Select Task-Master Project ───────────────────┐
│                                           ✕      │
├──────────────────────────────────────────────────┤
│ 🟢 file-processing-redesign                      │
│    /Users/you/workspace/file-processing-redesign │
│    🟢 Active • 12 tasks • Branch: feature/auth   │
├──────────────────────────────────────────────────┤
│ ⚫ auth-system                                    │
│    /Users/you/projects/auth-system               │
│    ⚫ Inactive • 5 tasks • Branch: main          │
├──────────────────────────────────────────────────┤
│ 🟢 dashboard-v2                                  │
│    /Users/you/work/dashboard-v2                  │
│    🟢 Active • 8 tasks • Branch: feature/charts │
├──────────────────────────────────────────────────┤
│                            [Use Task-Master Prompt] │
└──────────────────────────────────────────────────┘
```

4. **Click "Use Task-Master Prompt"** - automatically copies the rendered prompt with all project context

### Cross-Platform Context

The browser extension works across:
- **Claude.ai** - AI chat interface
- **ChatGPT** - OpenAI interface
- **GitHub** - Code reviews and issues
- **Notion** - Documentation
- **Linear** - Project management
- **Gmail** - Email composition

## 🧠 **How Project Detection Works**

### Discovery Process
1. **Scans common directories**: `~/`, `~/Projects`, `~/Code`, `~/workspace`, etc.
2. **Looks for Task-Master indicators**:
   - `task-master/` directory
   - `.task-master/` directory  
   - `task-master.yml` config file
   - `tasks/` directory with `.md` files

3. **Analyzes project structure**:
   - Git repository information
   - Task file count and recent activity
   - PRD locations and documentation

### Auto-Detection Logic
```
Current Directory: /Users/you/workspace/file-processing-redesign

1. Check if directory is registered project ✅
2. Check if subdirectory of registered project ✅  
3. Try to discover new project in current directory ✅
4. Fall back to manual selection ❌
```

### Project Registry Storage
Projects are stored in `~/.prompt_manager_projects.json`:
```json
{
  "projects": {
    "a1b2c3d4": {
      "id": "a1b2c3d4",
      "name": "file-processing-redesign", 
      "path": "/Users/you/workspace/file-processing-redesign",
      "task_master_dir": "/Users/you/workspace/file-processing-redesign/task-master",
      "git_info": {
        "branch": "feature/unified-processing",
        "remote": "git@github.com:you/file-processing-redesign.git"
      },
      "task_count": 12,
      "active": true,
      "last_used": "2025-01-24T10:30:00Z"
    }
  },
  "current_project": "a1b2c3d4"
}
```

## 📊 **Context Extraction Examples**

### Example 1: Feature Development Project
```markdown
# task-master/active/implement-auth-system.md
Status: In Progress
PRD: /docs/auth-prd.md
DOCS: /docs/auth/

Requirements:
- OAuth2 integration with Google/GitHub
- JWT token management
- Role-based permissions

Success Criteria:
- All authentication flows working
- Security audit passed
- 100% test coverage
```

**Extracted Variables**:
```
PRD_LOCATION=/docs/auth-prd.md
FEATURE_DOCS=/docs/auth/
PROJECT_REQUIRMENTS=1. OAuth2 integration with Google/GitHub
2. JWT token management  
3. Role-based permissions
PROJECT_SUCCESS_CRITERIA=- All authentication flows working
- Security audit passed
- 100% test coverage
CUSTOM_PROMPT=Working on: implement-auth-system.md
Task Status: In Progress
Branch: feature/auth-system
```

### Example 2: Bug Fix Project
```markdown
# task-master/active/fix-file-upload-bug.md
Status: Active
PRD: /docs/file-processing-prd.md

Requirements:
- Fix memory leak in file processor
- Handle large file uploads properly
- Add proper error handling
```

**Extracted Variables**:
```
PRD_LOCATION=/docs/file-processing-prd.md
PROJECT_REQUIRMENTS=1. Fix memory leak in file processor
2. Handle large file uploads properly
3. Add proper error handling
CUSTOM_PROMPT=Working on: fix-file-upload-bug.md
Task Status: Active
Branch: hotfix/file-upload
```

## 🔄 **Workflow Integration**

### Team Workflow
```bash
# Team lead sets up projects
pmcli --list-projects  # Discovers team projects

# Developers use auto-detection
cd /project/feature-branch
pmcli  # Auto-detects correct project context

# Result: Everyone gets consistent, accurate project context
```

### CI/CD Integration
```bash
# In your CI pipeline
python3 src/project_registry.py auto-detect --cwd $PWD
pmcli --api --project-id $(cat .current_project_id)
```

### IDE Integration
```json
// VS Code tasks.json
{
  "label": "Task-Master Prompt", 
  "type": "shell",
  "command": "${workspaceFolder}/promptManager/tm-prompt",
  "group": "build"
}
```

## 🚀 **Benefits**

### For Individual Users
- **No manual context switching** - auto-detects current project
- **Always accurate context** - pulls latest task files and PRDs
- **Cross-platform consistency** - same context in CLI and browser
- **Time savings** - eliminates 2-3 minutes of manual setup per session

### For Teams  
- **Standardized contexts** - everyone gets the same project variables
- **Onboarding simplification** - new team members auto-discover projects
- **Documentation consistency** - PRD locations and requirements always current
- **Reduced errors** - no more copy-paste mistakes in file paths

### Compared to Alternatives
- **vs Manual**: 10x faster, no copy-paste errors
- **vs Single Project**: Handles real-world multi-project workflows  
- **vs Static Configs**: Always reflects current project state
- **vs Team Wikis**: Self-updating, always accessible

This system transforms Task-Master from a single-project tool to a comprehensive multi-project workflow solution that scales with your development complexity.