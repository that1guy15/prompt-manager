#!/usr/bin/env python3

import json
import os
import sys
import argparse
import subprocess
import glob
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


def show_banner():
    """Display the Prompt Manager banner with cyan to violet gradient"""
    # ANSI color codes
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Gradient colors from cyan to violet
    CYAN = '\033[38;5;51m'      # Bright cyan
    CYAN_BLUE = '\033[38;5;45m' # Cyan-blue
    BLUE = '\033[38;5;39m'      # Blue
    BLUE_PURPLE = '\033[38;5;63m' # Blue-purple
    PURPLE = '\033[38;5;93m'    # Purple
    VIOLET = '\033[38;5;129m'   # Violet
    
    banner = f"""
{CYAN}═══════════════════════════════════════════════════════════════════{RESET}

{CYAN}{BOLD}  ____                            _         {RESET}
{CYAN_BLUE}{BOLD} |  _ \\ _ __ ___  _ __ ___  _ __ | |_ _   _ {RESET}
{BLUE}{BOLD} | |_) | '__/ _ \\| '_ ` _ \\| '_ \\| __| | | |{RESET}
{BLUE_PURPLE}{BOLD} |  __/| | | (_) | | | | | | |_) | |_| |_| |{RESET}
{PURPLE}{BOLD} |_|   |_|  \\___/|_| |_| |_| .__/ \\__|\\__, |{RESET}
{VIOLET}{BOLD}                           |_|        |___/ {RESET}

  Build context aware prompts effortlessly

{VIOLET}═══════════════════════════════════════════════════════════════════{RESET}
    """
    print(banner)


def get_api_url(args_api_url: str = None) -> str:
    """Get API URL from args, environment, or prompt user"""
    # First check command line argument
    if args_api_url and args_api_url != "http://localhost:5000/api":
        return args_api_url
    
    # Then check environment variable  
    env_url = os.environ.get("PROMPT_API_URL")
    if env_url:
        return env_url
    
    # Check if localhost API is reachable
    default_url = "http://localhost:5000/api"
    try:
        import requests
        response = requests.get(f"{default_url.rstrip('/api')}/health", timeout=2)
        if response.status_code == 200:
            return default_url
    except:
        pass
    
    # Prompt user for API URL
    print("\n🔗 API Server Configuration")
    print("=" * 50)
    print("The Prompt Manager API server is not reachable at the default location.")
    print("Please provide the API server URL, or press Enter to use localhost default.")
    print()
    
    while True:
        user_input = input(f"API URL [{default_url}]: ").strip()
        api_url = user_input if user_input else default_url
        
        # Validate URL format
        if not api_url.startswith(('http://', 'https://')):
            print("❌ Please enter a valid URL starting with http:// or https://")
            continue
            
        # Test connection
        print(f"🔍 Testing connection to {api_url}...")
        try:
            import requests
            test_url = api_url.replace('/api', '').rstrip('/') + '/health'
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print("✅ Connection successful!")
                
                # Offer to save as environment variable
                save_env = input("\n💾 Save this URL as default? (y/N): ").strip().lower()
                if save_env == 'y':
                    print(f"\n📝 Add this to your ~/.bashrc or ~/.zshrc:")
                    print(f"export PROMPT_API_URL=\"{api_url}\"")
                
                return api_url
            else:
                print(f"❌ Server responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        
        retry = input("\n🔄 Try a different URL? (Y/n): ").strip().lower()
        if retry == 'n':
            print("⚠️  Using provided URL without verification...")
            return api_url


class PromptManager:
    def __init__(self, data_file: str = "prompts.json"):
        self.data_file = data_file
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"prompts": [], "categories": [], "variables": {}}
    
    def _save_prompts(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.prompts, f, indent=2)
    
    def _extract_variables(self, content: str) -> List[str]:
        return list(set(re.findall(r'\{(\w+)\}', content)))
    
    def _validate_variables(self, content: str):
        variables = self._extract_variables(content)
        missing_vars = []
        
        for var in variables:
            if var not in self.prompts.get("variables", {}):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Warning: The following variables are not defined: {', '.join(missing_vars)}")
            print("Please define them using: ./prompt_manager.py var add <name> <description> [default_value]")
        
        return missing_vars
    
    def add_prompt(self, title: str, content: str, category: str = "general", tags: List[str] = None):
        if tags is None:
            tags = []
        
        self._validate_variables(content)
        
        prompt_id = len(self.prompts["prompts"]) + 1
        new_prompt = {
            "id": prompt_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags,
            "created_at": datetime.now().isoformat(),
            "used_count": 0,
            "variables": self._extract_variables(content)
        }
        
        self.prompts["prompts"].append(new_prompt)
        
        if category not in self.prompts["categories"]:
            self.prompts["categories"].append(category)
        
        self._save_prompts()
        print(f"Added prompt '{title}' with ID {prompt_id}")
    
    def import_prompt_from_json(self, json_file: str):
        try:
            with open(json_file, 'r') as f:
                prompt_data = json.load(f)
            
            if isinstance(prompt_data, list):
                for prompt in prompt_data:
                    self._import_single_prompt(prompt)
            else:
                self._import_single_prompt(prompt_data)
                
        except FileNotFoundError:
            print(f"File {json_file} not found.")
        except json.JSONDecodeError:
            print(f"Invalid JSON in file {json_file}.")
        except Exception as e:
            print(f"Error importing {json_file}: {e}")
    
    def _import_single_prompt(self, prompt_data: Dict):
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in prompt_data:
                print(f"Skipping prompt: missing required field '{field}'")
                return
        
        self._validate_variables(prompt_data['content'])
        
        prompt_id = len(self.prompts["prompts"]) + 1
        new_prompt = {
            "id": prompt_id,
            "title": prompt_data['title'],
            "content": prompt_data['content'],
            "category": prompt_data.get('category', 'general'),
            "tags": prompt_data.get('tags', []),
            "created_at": prompt_data.get('created_at', datetime.now().isoformat()),
            "used_count": prompt_data.get('used_count', 0),
            "variables": self._extract_variables(prompt_data['content'])
        }
        
        self.prompts["prompts"].append(new_prompt)
        
        category = new_prompt['category']
        if category not in self.prompts["categories"]:
            self.prompts["categories"].append(category)
        
        print(f"Imported prompt '{new_prompt['title']}' with ID {prompt_id}")
    
    def import_from_directory(self, directory: str):
        json_files = glob.glob(os.path.join(directory, "*.json"))
        if not json_files:
            print(f"No JSON files found in {directory}")
            return
        
        print(f"Found {len(json_files)} JSON files")
        for json_file in json_files:
            print(f"Importing {json_file}...")
            self.import_prompt_from_json(json_file)
        
        self._save_prompts()
        print(f"Import complete. Imported from {len(json_files)} files.")
    
    def import_from_files(self, file_list: List[str]):
        imported_count = 0
        for json_file in file_list:
            if os.path.exists(json_file):
                print(f"Importing {json_file}...")
                self.import_prompt_from_json(json_file)
                imported_count += 1
            else:
                print(f"File not found: {json_file}")
        
        if imported_count > 0:
            self._save_prompts()
            print(f"Import complete. Imported from {imported_count} files.")
    
    def list_prompts(self, category: str = None, tag: str = None, search: str = None):
        filtered_prompts = self.prompts["prompts"]
        
        if category:
            filtered_prompts = [p for p in filtered_prompts if p["category"] == category]
        
        if tag:
            filtered_prompts = [p for p in filtered_prompts if tag in p["tags"]]
        
        if search:
            search_lower = search.lower()
            filtered_prompts = [p for p in filtered_prompts 
                              if search_lower in p["title"].lower() or 
                                 search_lower in p["content"].lower()]
        
        if not filtered_prompts:
            print("No prompts found matching criteria.")
            return
        
        print(f"\n{'ID':<4} {'Title':<30} {'Category':<15} {'Tags':<20} {'Used':<5}")
        print("-" * 75)
        
        for prompt in filtered_prompts:
            tags_str = ", ".join(prompt["tags"][:3])
            if len(prompt["tags"]) > 3:
                tags_str += "..."
            
            print(f"{prompt['id']:<4} {prompt['title'][:28]:<30} "
                  f"{prompt['category']:<15} {tags_str:<20} {prompt['used_count']:<5}")
    
    def get_prompt(self, prompt_id: int) -> Optional[Dict]:
        for prompt in self.prompts["prompts"]:
            if prompt["id"] == prompt_id:
                return prompt
        return None
    
    def copy_prompt(self, prompt_id: int, variables: Dict[str, str] = None):
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            print(f"Prompt with ID {prompt_id} not found.")
            return
        
        content = prompt["content"]
        prompt_vars = prompt.get("variables", [])
        system_vars = self.prompts.get("variables", {})
        
        final_variables = {}
        for var in prompt_vars:
            if variables and var in variables:
                final_variables[var] = variables[var]
            elif var in system_vars and system_vars[var].get("default_value"):
                final_variables[var] = system_vars[var]["default_value"]
                print(f"Using default value for '{var}': {final_variables[var]}")
            else:
                print(f"No value provided for variable '{var}'")
                return
        
        for var, value in final_variables.items():
            content = content.replace(f"{{{var}}}", value)
            if var in system_vars:
                system_vars[var]["used_count"] = system_vars[var].get("used_count", 0) + 1
        
        try:
            if sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=content, text=True, check=True)
            elif sys.platform.startswith("linux"):
                subprocess.run(["xclip", "-selection", "clipboard"], input=content, text=True, check=True)
            else:
                print("Clipboard functionality not supported on this platform.")
                print("\nPrompt content:")
                print("-" * 40)
                print(content)
                return
            
            prompt["used_count"] += 1
            self._save_prompts()
            print(f"Copied prompt '{prompt['title']}' to clipboard!")
            
        except subprocess.CalledProcessError:
            print("Failed to copy to clipboard. Here's the content:")
            print("-" * 40)
            print(content)
    
    def show_prompt(self, prompt_id: int):
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            print(f"Prompt with ID {prompt_id} not found.")
            return
        
        print(f"\nTitle: {prompt['title']}")
        print(f"Category: {prompt['category']}")
        print(f"Tags: {', '.join(prompt['tags'])}")
        print(f"Used: {prompt['used_count']} times")
        print(f"Created: {prompt['created_at']}")
        
        variables = prompt.get('variables', [])
        if variables:
            print(f"Variables: {', '.join(variables)}")
        
        print("\nContent:")
        print("-" * 40)
        print(prompt['content'])
    
    def delete_prompt(self, prompt_id: int):
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            print(f"Prompt with ID {prompt_id} not found.")
            return
        
        self.prompts["prompts"] = [p for p in self.prompts["prompts"] if p["id"] != prompt_id]
        self._save_prompts()
        print(f"Deleted prompt '{prompt['title']}'")
    
    def list_categories(self):
        if not self.prompts["categories"]:
            print("No categories found.")
            return
        
        print("Categories:")
        for cat in sorted(self.prompts["categories"]):
            count = len([p for p in self.prompts["prompts"] if p["category"] == cat])
            print(f"  {cat} ({count} prompts)")
    
    def add_variable(self, name: str, description: str, default_value: str = None):
        if "variables" not in self.prompts:
            self.prompts["variables"] = {}
        
        self.prompts["variables"][name] = {
            "description": description,
            "default_value": default_value,
            "created_at": datetime.now().isoformat(),
            "used_count": 0
        }
        
        self._save_prompts()
        print(f"Added variable '{name}'")
    
    def list_variables(self):
        variables = self.prompts.get("variables", {})
        if not variables:
            print("No variables defined.")
            return
        
        print(f"\n{'Name':<20} {'Description':<40} {'Default':<15} {'Used':<5}")
        print("-" * 85)
        
        for name, var_data in variables.items():
            default = var_data.get('default_value', 'None')
            if default and len(default) > 13:
                default = default[:10] + "..."
            
            print(f"{name:<20} {var_data['description'][:38]:<40} "
                  f"{default:<15} {var_data['used_count']:<5}")
    
    def update_variable(self, name: str, description: str = None, default_value: str = None):
        variables = self.prompts.get("variables", {})
        if name not in variables:
            print(f"Variable '{name}' not found.")
            return
        
        if description:
            variables[name]["description"] = description
        if default_value is not None:
            variables[name]["default_value"] = default_value
        
        self._save_prompts()
        print(f"Updated variable '{name}'")
    
    def delete_variable(self, name: str):
        variables = self.prompts.get("variables", {})
        if name not in variables:
            print(f"Variable '{name}' not found.")
            return
        
        used_in_prompts = []
        for prompt in self.prompts["prompts"]:
            if name in prompt.get("variables", []):
                used_in_prompts.append(prompt["title"])
        
        if used_in_prompts:
            print(f"Warning: Variable '{name}' is used in the following prompts:")
            for title in used_in_prompts:
                print(f"  - {title}")
            response = input("Delete anyway? (y/N): ")
            if response.lower() != 'y':
                print("Deletion cancelled.")
                return
        
        del variables[name]
        self._save_prompts()
        print(f"Deleted variable '{name}'")


def show_help_content(topic=None):
    """Show interactive help content"""
    help_topics = {
        'quick-start': """
🚀 QUICK START GUIDE

1. Add your first prompt:
   ./prompt_manager.py add --manual "My Prompt" "Content here" -c category

2. List your prompts:
   ./prompt_manager.py list

3. Copy a prompt to clipboard:
   ./prompt_manager.py copy 1

4. For Task-Master integration:
   pmcli

📖 Full guide: docs/QUICK_START.md
        """,
        
        'commands': """
🎮 COMMAND REFERENCE

PROMPT MANAGEMENT:
• add --manual "title" "content"     Add prompt manually
• add --file prompt.json             Import from JSON file
• list [-c category] [-t tag] [-s search]  List/filter prompts
• copy ID [-v var=value]             Copy prompt with variables
• show ID                            Show prompt details
• delete ID                          Delete prompt

VARIABLES:
• var add name "desc" [default]      Add variable
• var list                           List all variables
• var update name -d "desc"          Update variable
• var delete name                    Delete variable

CATEGORIES & SEARCH:
• categories                         List all categories
• list -c development               Filter by category
• list -t code-review               Filter by tag  
• list -s "search term"             Search content

CONFIGURATION:
• --api-url URL                      Set API server URL
• export PROMPT_API_URL=URL          Set via environment variable

📖 Full guide: docs/CLI_USAGE.md
        """,
        
        'task-master': """
🔧 TASK-MASTER INTEGRATION

QUICK COMMANDS:
• pmcli                        Auto-detect project & copy context
• pmcli --list-projects        Show available projects
• pmcli --select-project       Choose project interactively

PROJECT MANAGEMENT:
• python3 src/project_registry.py add "Name" /path    Add project
• python3 src/project_registry.py list               List projects
• python3 src/project_registry.py disable project-id Hide project

WHAT IT DOES:
✅ Auto-fills PRD locations, requirements, success criteria
✅ Includes current task, git branch, project context
✅ Works with multiple projects seamlessly

📖 Full guide: docs/TASK_MASTER_INTEGRATION.md
        """,
        
        'browser': """
🌐 BROWSER EXTENSION

SETUP:
1. Start API: python3 src/prompt_api.py
2. Chrome → chrome://extensions/
3. Enable "Developer mode"
4. "Load unpacked" → select browser_extension/
5. Visit Claude.ai → See magic! ✨

USAGE:
• Ctrl+Shift+P                      Quick access popup
• Click 📂                          Choose Task-Master project
• Focus text field                   Auto-suggestions appear
• Right-click icon → Options         Full settings

WORKS ON:
Claude.ai, ChatGPT, GitHub, Notion, Linear, Slack

📖 Full guide: docs/BROWSER_EXTENSION.md
        """,
        
        'examples': """
💡 COMMON EXAMPLES

CODE REVIEW:
./prompt_manager.py add --manual "Code Review" "Review {code} for security and best practices" -c dev
./prompt_manager.py copy 1 -v code="function login() { return true; }"

BUG INVESTIGATION:  
./prompt_manager.py add --manual "Debug" "Debug: {issue}. Error: {error}" -c debug
./prompt_manager.py copy 2 -v issue="Login fails" error="TypeError"

DAILY STANDUP:
./prompt_manager.py add --manual "Standup" "Help with standup: yesterday, today, blockers" -c productivity
./prompt_manager.py copy 3

TASK-MASTER PROJECT:
cd ~/my-project
pmcli  # Instant project context with PRD, requirements, tasks

📖 More examples: docs/examples/
        """,
        
        'troubleshooting': """
🆘 TROUBLESHOOTING

COMMAND NOT FOUND:
chmod +x prompt_manager.py pmcli

CLIPBOARD NOT WORKING:
• macOS: Should work automatically
• Linux: sudo apt-get install xclip
• Windows: Content displays instead

NO PROJECTS FOUND:
python3 src/project_registry.py add "My Project" /path/to/project

BROWSER EXTENSION ISSUES:
• Check API running: python3 src/prompt_api.py
• Verify extension permissions in Chrome
• Test connection in extension options

IMPORT ERRORS:
• Validate JSON with JSONLint
• Check required fields: title, content

📖 Full troubleshooting: docs/TROUBLESHOOTING.md
        """
    }
    
    if topic is None:
        print("""
💡 PROMPT MANAGER HELP

Available help topics:
• ./prompt_manager.py help quick-start     🚀 5-minute getting started
• ./prompt_manager.py help commands        🎮 All CLI commands  
• ./prompt_manager.py help task-master     🔧 Task-Master integration
• ./prompt_manager.py help browser         🌐 Browser extension setup
• ./prompt_manager.py help examples        💡 Common use cases
• ./prompt_manager.py help troubleshooting 🆘 Fix common issues

For command-specific help:
• ./prompt_manager.py --help              📖 Command line options
• pmcli --help                      🔧 Task-Master help
• python3 src/project_registry.py --help  📂 Project management

Full documentation: docs/ directory
        """)
    elif topic in help_topics:
        print(help_topics[topic])
    else:
        print(f"❌ Unknown help topic: {topic}")
        print("Available topics: " + ", ".join(help_topics.keys()))

def main():
    parser = argparse.ArgumentParser(description="AI Prompt Manager")
    parser.add_argument("--api-url", default=os.environ.get("PROMPT_API_URL", "http://localhost:5000/api"), 
                       help="API server URL (default: http://localhost:5000/api, or PROMPT_API_URL env var)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Help command
    help_parser = subparsers.add_parser("help", help="Show interactive help")
    help_parser.add_argument("topic", nargs="?", help="Help topic (quick-start, commands, task-master, browser, examples, troubleshooting)")
    
    # Add prompt
    add_parser = subparsers.add_parser("add", help="Add a new prompt")
    add_group = add_parser.add_mutually_exclusive_group(required=True)
    add_group.add_argument("--manual", nargs=2, metavar=('TITLE', 'CONTENT'), help="Add prompt manually")
    add_group.add_argument("--file", help="Import single JSON file")
    add_group.add_argument("--dir", help="Import all JSON files from directory")
    add_group.add_argument("--files", nargs="+", help="Import multiple JSON files")
    add_parser.add_argument("-c", "--category", default="general", help="Category (for manual add only)")
    add_parser.add_argument("-t", "--tags", nargs="*", default=[], help="Tags (for manual add only)")
    
    # List prompts
    list_parser = subparsers.add_parser("list", help="List prompts")
    list_parser.add_argument("-c", "--category", help="Filter by category")
    list_parser.add_argument("-t", "--tag", help="Filter by tag")
    list_parser.add_argument("-s", "--search", help="Search in title and content")
    
    # Copy prompt
    copy_parser = subparsers.add_parser("copy", help="Copy prompt to clipboard")
    copy_parser.add_argument("id", type=int, help="Prompt ID")
    copy_parser.add_argument("-v", "--variables", nargs="*", help="Variables in key=value format")
    
    # Show prompt
    show_parser = subparsers.add_parser("show", help="Show prompt details")
    show_parser.add_argument("id", type=int, help="Prompt ID")
    
    # Delete prompt
    delete_parser = subparsers.add_parser("delete", help="Delete a prompt")
    delete_parser.add_argument("id", type=int, help="Prompt ID")
    
    # List categories
    subparsers.add_parser("categories", help="List all categories")
    
    # Variable management
    var_parser = subparsers.add_parser("var", help="Manage template variables")
    var_subparsers = var_parser.add_subparsers(dest="var_command", help="Variable commands")
    
    # Add variable
    var_add_parser = var_subparsers.add_parser("add", help="Add a new variable")
    var_add_parser.add_argument("name", help="Variable name")
    var_add_parser.add_argument("description", help="Variable description")
    var_add_parser.add_argument("default", nargs="?", help="Default value")
    
    # List variables
    var_subparsers.add_parser("list", help="List all variables")
    
    # Update variable
    var_update_parser = var_subparsers.add_parser("update", help="Update a variable")
    var_update_parser.add_argument("name", help="Variable name")
    var_update_parser.add_argument("-d", "--description", help="New description")
    var_update_parser.add_argument("--default", help="New default value")
    
    # Delete variable
    var_delete_parser = var_subparsers.add_parser("delete", help="Delete a variable")
    var_delete_parser.add_argument("name", help="Variable name")
    
    args = parser.parse_args()
    
    # Show banner for interactive commands (not for help)
    if args.command and args.command != "help":
        show_banner()
    
    if not args.command:
        show_banner()
        parser.print_help()
        return
    
    # Get API URL with prompting if needed
    api_url = get_api_url(args.api_url)
    
    pm = PromptManager()
    
    if args.command == "help":
        show_help_content(args.topic)
        return
    
    if args.command == "add":
        if args.manual:
            pm.add_prompt(args.manual[0], args.manual[1], args.category, args.tags)
        elif args.file:
            pm.import_prompt_from_json(args.file)
            pm._save_prompts()
        elif args.dir:
            pm.import_from_directory(args.dir)
        elif args.files:
            pm.import_from_files(args.files)
    
    elif args.command == "list":
        pm.list_prompts(args.category, args.tag, args.search)
    
    elif args.command == "copy":
        variables = {}
        if args.variables:
            for var in args.variables:
                if "=" in var:
                    key, value = var.split("=", 1)
                    variables[key] = value
        pm.copy_prompt(args.id, variables)
    
    elif args.command == "show":
        pm.show_prompt(args.id)
    
    elif args.command == "delete":
        pm.delete_prompt(args.id)
    
    elif args.command == "categories":
        pm.list_categories()
    
    elif args.command == "var":
        if not args.var_command:
            var_parser.print_help()
        elif args.var_command == "add":
            pm.add_variable(args.name, args.description, args.default)
        elif args.var_command == "list":
            pm.list_variables()
        elif args.var_command == "update":
            pm.update_variable(args.name, args.description, args.default)
        elif args.var_command == "delete":
            pm.delete_variable(args.name)


if __name__ == "__main__":
    main()