# AI Prompt Manager

A command-line tool for organizing, managing, and quickly accessing AI prompts with template variable support.

## Features

- **Prompt Organization**: Categorize and tag prompts for easy retrieval
- **Variable Management**: Define reusable variables with default values
- **JSON Import/Export**: Import single files, directories, or multiple files
- **Quick Copy**: Copy prompts to clipboard with variable substitution
- **Search & Filter**: Find prompts by category, tags, or content
- **Usage Tracking**: Track how often prompts and variables are used

## Installation

1. Ensure Python 3 is installed
2. Make the script executable:
   ```bash
   chmod +x prompt_manager.py
   ```

## CLI Commands

### Prompt Management

#### Add Prompts

```bash
# Add manually
./prompt_manager.py add --manual "Title" "Content" -c category -t tag1 tag2

# Import from JSON file
./prompt_manager.py add --file prompt.json

# Import all JSON files from directory
./prompt_manager.py add --dir /path/to/prompts/

# Import multiple specific files
./prompt_manager.py add --files file1.json file2.json file3.json
```

#### List Prompts

```bash
# List all prompts
./prompt_manager.py list

# Filter by category
./prompt_manager.py list -c development

# Filter by tag
./prompt_manager.py list -t security

# Search in title and content
./prompt_manager.py list -s "code review"
```

#### Copy Prompt to Clipboard

```bash
# Copy with default variable values
./prompt_manager.py copy 1

# Copy with custom variable values
./prompt_manager.py copy 1 -v code="def hello():" context="Python function"
```

#### Show Prompt Details

```bash
./prompt_manager.py show 1
```

#### Delete Prompt

```bash
./prompt_manager.py delete 1
```

#### List Categories

```bash
./prompt_manager.py categories
```

### Variable Management

Variables are placeholders in prompts that can be replaced with actual values when copying.

#### Add Variable

```bash
# Add variable with default value
./prompt_manager.py var add endpoint "API endpoint URL" "/api/v1/users"

# Add variable without default
./prompt_manager.py var add code "Code snippet to review"
```

#### List Variables

```bash
./prompt_manager.py var list
```

#### Update Variable

```bash
# Update description only
./prompt_manager.py var update endpoint -d "New description"

# Update default value only
./prompt_manager.py var update endpoint --default "/api/v2/users"

# Update both
./prompt_manager.py var update endpoint -d "API endpoint" --default "/api/v3/users"
```

#### Delete Variable

```bash
./prompt_manager.py var delete endpoint
```

## JSON Import Format

### Single Prompt

```json
{
  "title": "Code Review Request",
  "content": "Please review {code} for security issues.\nContext: {context}",
  "category": "development",
  "tags": ["code-review", "security"],
  "created_at": "2025-01-20T10:00:00Z",
  "used_count": 0
}
```

### Multiple Prompts

```json
[
  {
    "title": "Bug Analysis",
    "content": "Analyze bug: {description}\nError: {error}",
    "category": "debugging",
    "tags": ["bug-fix"]
  },
  {
    "title": "Feature Design",
    "content": "Design feature: {feature_name}",
    "category": "planning",
    "tags": ["architecture"]
  }
]
```

## Usage Examples

### Example 1: Quick Code Review

```bash
# Add code review prompt
./prompt_manager.py add --manual "Code Review" "Review {code} for {issue_type}" -c dev -t review

# Define variables
./prompt_manager.py var add code "Code to review"
./prompt_manager.py var add issue_type "Type of issue" "security vulnerabilities"

# Copy prompt with custom code
./prompt_manager.py copy 1 -v code="SELECT * FROM users" issue_type="SQL injection"
```

### Example 2: Import Workflow

```bash
# Create prompts directory
mkdir my_prompts

# Import all prompts from directory
./prompt_manager.py add --dir my_prompts/

# List imported prompts
./prompt_manager.py list
```

### Example 3: Project-Specific Prompts

```bash
# Add project management prompt
./prompt_manager.py add --manual "Sprint Planning" "Plan sprint for {project} with {team_size} developers" -c project -t planning

# Set default values
./prompt_manager.py var add project "Project name" "MyApp"
./prompt_manager.py var add team_size "Number of developers" "5"

# Use prompt
./prompt_manager.py copy 1
```

## Variable System

### How Variables Work

1. **Definition**: Variables are defined using `{variable_name}` in prompt content
2. **Validation**: System checks all variables are defined when adding prompts
3. **Defaults**: Variables can have default values used when not specified
4. **Substitution**: Variables are replaced when copying prompts to clipboard

### Best Practices

1. **Consistent Naming**: Use descriptive variable names (e.g., `api_endpoint` not `ep`)
2. **Default Values**: Set sensible defaults for commonly used values
3. **Documentation**: Use clear descriptions for variables
4. **Reusability**: Design variables to work across multiple prompts

## Data Storage

All data is stored in `prompts.json` in the current directory, including:
- Prompts with their content, category, and tags
- Variables with descriptions and default values
- Usage statistics for both prompts and variables

## Platform Support

- **macOS**: Full clipboard support via `pbcopy`
- **Linux**: Clipboard support via `xclip` (must be installed)
- **Windows**: Manual copy (clipboard not supported)

## Tips

1. **Organize by Project**: Use categories like "project-name" for project-specific prompts
2. **Tag Strategically**: Use tags like "urgent", "review", "test" for quick filtering
3. **Template Everything**: Use variables for any value that changes between uses
4. **Regular Backups**: Back up your `prompts.json` file regularly

## Troubleshooting

### "Variable not defined" Warning
- Define the variable using `./prompt_manager.py var add <name> <description>`
- Or provide a value when copying: `./prompt_manager.py copy 1 -v var_name="value"`

### Clipboard Not Working
- **Linux**: Install xclip: `sudo apt-get install xclip`
- **Windows**: Copy will display prompt content instead

### Import Errors
- Ensure JSON files are properly formatted
- Check that required fields (title, content) are present
- Use JSONLint or similar tool to validate JSON

## License

This tool is provided as-is for personal and commercial use.