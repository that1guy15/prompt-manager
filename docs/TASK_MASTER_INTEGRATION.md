# Task-Master Integration Guide

## Quick Start

The Task-Master integration automatically extracts project context from your Task-Master files and populates prompt variables, eliminating manual copy-paste.

### Basic Usage

```bash
# From your project directory with Task-Master
pmcli

# Output:
🔍 Extracting Task-Master context...
💡 Rendering prompt 4...
✅ Generated prompt: Task Master Project Continuation
📋 Copied to clipboard!

💡 Quick summary of context:
   📂 Active Task: implement-auth-system.md
   🌿 Branch: feature/user-authentication
   📄 PRD: /app/uploads/redesign_v3/PRD_TASK_MASTER.md

🚀 Ready to paste into Claude Code!
```

### What It Does

1. **Finds Task-Master** in your project (looks for common locations)
2. **Extracts context** from task files, PRDs, and project structure
3. **Auto-fills variables** like PRD_LOCATION, FEATURE_DOCS, PROJECT_REQUIREMENTS
4. **Copies to clipboard** ready for Claude Code

### Supported Task-Master Formats

The extractor looks for these patterns in your task files:

```markdown
# Task: Implement User Authentication
Status: In Progress
PRD: /app/uploads/redesign_v3/PRD_TASK_MASTER.md
DOCS: /app/uploads/redesign_v3/docs

Requirements:
- Unified authentication system
- OAuth2 integration
- Session management

Success Criteria:
- All authentication flows working
- Security audit passed
- 100% test coverage
```

### Variable Extraction

| Prompt Variable | Extracted From |
|----------------|----------------|
| PRD_LOCATION | `PRD:` line or task-master.yml |
| FEATURE_DOCS | `DOCS:` line or docs directory |
| PROJECT_REQUIRMENTS | Requirements section |
| PROJECT_SUCCESS_CRITERIA | Success Criteria section |
| CUSTOM_PROMPT | Git branch + task status |

### Advanced Usage

```bash
# Show extracted context
pmcli --show-context

# Use different prompt
pmcli --prompt-id 2  # Bug Analysis prompt

# Dry run (show without copying)
pmcli --dry-run

# Use with API running
pmcli --api
```

### Integration with Your Workflow

#### Option 1: Shell Alias
```bash
# Add to ~/.bashrc or ~/.zshrc
alias tm='~/promptManager/tm-prompt'

# Usage
cd /your/project
tm  # Instantly copies Task-Master context prompt
```

#### Option 2: Git Hook
```bash
# .git/hooks/post-checkout
#!/bin/bash
if [ -d "task-master" ]; then
    ~/promptManager/tm-prompt --show-context
fi
```

#### Option 3: VS Code Task
```json
// .vscode/tasks.json
{
  "label": "Copy Task-Master Prompt",
  "type": "shell",
  "command": "${workspaceFolder}/promptManager/tm-prompt",
  "presentation": {
    "reveal": "silent",
    "showReuseMessage": false
  }
}
```

### Task-Master Configuration

For best results, add a `task-master.yml` to your project:

```yaml
# task-master.yml
project:
  name: "File Processing Redesign"
  description: "Unified file processing architecture"

prd_location: "/app/uploads/redesign_v3/PRD_TASK_MASTER.md"
docs_directory: "/app/uploads/redesign_v3/docs"

default_requirements:
  - Unified file processing architecture with UnifiedFileManager
  - Cloud storage unification across all environments
  - Security architecture with private buckets

success_criteria:
  - All file availability issues resolved
  - Development/production parity achieved
  - Security hardened with proper authorization
```

### How It Enhances Your Claude Code Workflow

**Before:**
1. Open Claude Code
2. Manually type Task-Master context
3. Copy file paths, requirements, etc.
4. Risk errors in paths or missing context

**After:**
1. Run `tm-prompt` 
2. Paste into Claude Code
3. All context automatically included

### Browser Extension Integration

The browser extension will automatically detect when you're in Claude Code and suggest the Task-Master prompt with pre-filled variables from your current project context.

### Troubleshooting

**"No Task-Master directory found"**
- Ensure you have a `task-master/` directory in your project
- Or set `TASK_MASTER_DIR` environment variable

**"Missing variables"**
- Check your task files include the expected sections
- Use `--show-context` to see what was extracted

**"Failed to copy to clipboard"**
- Install `pbcopy` (macOS) or `xclip` (Linux)
- Use `--dry-run` to see the prompt content