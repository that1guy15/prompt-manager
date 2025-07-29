#!/usr/bin/env python3

"""
Task-Master Prompt Integration CLI
Professional CLI for Task-Master context extraction and prompt generation
"""

import sys
import os
import subprocess
import json
import argparse
from pathlib import Path

# Add package to path for development
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_manager.context_extractor import TaskMasterContextExtractor
from prompt_manager.core import PromptManager
from prompt_manager.project_registry import ProjectRegistry
import requests


def show_tm_banner():
    """Display the Task-Master integration banner with cyan to violet gradient"""
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


def get_api_url_tm(args_api_url: str = None) -> str:
    """Get API URL from args, environment, or prompt user for pmcli"""
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
        response = requests.get(f"{default_url.rstrip('/api')}/health", timeout=2)
        if response.status_code == 200:
            return default_url
    except:
        pass
    
    # Prompt user for API URL
    print("\n🔗 Task-Master Integration Setup")
    print("=" * 50)
    print("The Prompt Manager API server is not reachable.")
    print("Please start the API server or provide a custom URL.")
    print()
    print("💡 To start the API server: prompt-api")
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
            test_url = api_url.replace('/api', '').rstrip('/') + '/health'
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print("✅ Connection successful!")
                return api_url
            else:
                print(f"❌ Server responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        
        retry = input("\n🔄 Try a different URL? (Y/n): ").strip().lower()
        if retry == 'n':
            print("⚠️  Using provided URL without verification...")
            return api_url


def copy_to_clipboard(content: str) -> bool:
    """Copy content to clipboard"""
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=content, text=True, check=True)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xclip", "-selection", "clipboard"], input=content, text=True, check=True)
        else:
            return False
        return True
    except:
        return False


def create_parser():
    """Create the argument parser for pmcli"""
    parser = argparse.ArgumentParser(
        prog="pmcli",
        description="🧶 Task-Master context extraction and prompt generation",
        epilog="Extract project context and generate AI-ready prompts"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 1.0.0"
    )
    
    parser.add_argument(
        '--prompt-id', '-p', 
        type=int, 
        default=4,
        help='Prompt ID to use (default: 4 - Task Master Project Continuation)'
    )
    
    parser.add_argument(
        '--api-url', 
        default=os.environ.get('PROMPT_API_URL', 'http://localhost:5000/api'),
        help='API server URL (default: http://localhost:5000/api, or PROMPT_API_URL env var)'
    )
    
    parser.add_argument(
        '--show-context', '-s', 
        action='store_true',
        help='Show extracted context'
    )
    
    parser.add_argument(
        '--dry-run', '-d', 
        action='store_true',
        help='Show prompt without copying to clipboard'
    )
    
    parser.add_argument(
        '--api', 
        action='store_true',
        help='Use API instead of direct access'
    )
    
    parser.add_argument(
        '--project-root', '-r', 
        help='Project root directory'
    )
    
    parser.add_argument(
        '--project-id', 
        help='Specific project ID to use'
    )
    
    parser.add_argument(
        '--list-projects', '-l', 
        action='store_true',
        help='List available projects'
    )
    
    parser.add_argument(
        '--select-project', 
        action='store_true',
        help='Interactively select a project'
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress the banner display'
    )
    
    return parser


def main():
    """Main pmcli CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show banner
    if not args.no_banner:
        show_tm_banner()
    
    try:
        # Get API URL with prompting if needed (only when using API mode)
        if args.api:
            api_url = get_api_url_tm(args.api_url)
            args.api_url = api_url
        
        # Initialize project registry
        registry = ProjectRegistry()
        
        # Handle project listing
        if args.list_projects:
            projects = registry.list_projects()
            if not projects:
                print("❌ No projects found.")
                print("💡 Add projects with: project-registry add \"Project Name\" /path/to/project")
                return 1
            
            print("\n📂 Available Projects:")
            print("-" * 50)
            for project in projects:
                status = "✅" if project.get('enabled', True) else "❌"
                print(f"{status} {project['name']} [{project['id']}]")
                print(f"   📁 {project['path']}")
                if project.get('task_master_dir'):
                    print(f"   📋 Task-Master: {project['task_master_dir']}")
                print()
            return 0
        
        # Auto-detect or select project
        current_project = None
        
        if args.project_id:
            current_project = registry.get_project(args.project_id)
            if not current_project:
                print(f"❌ Project with ID '{args.project_id}' not found")
                return 1
        elif args.select_project:
            projects = registry.list_projects()
            if not projects:
                print("❌ No projects found.")
                return 1
            
            print("\n📂 Select a project:")
            for i, project in enumerate(projects, 1):
                status = "✅" if project.get('enabled', True) else "❌"
                print(f"{i}. {status} {project['name']}")
            
            try:
                choice = int(input("\nEnter project number: ")) - 1
                if 0 <= choice < len(projects):
                    current_project = projects[choice]
                else:
                    print("❌ Invalid selection")
                    return 1
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Selection cancelled")
                return 1
        else:
            # Auto-detect current project
            current_project = registry.auto_detect_current_project()
        
        if not current_project:
            print("❌ No project detected.")
            print("💡 Run with --list-projects to see available projects")
            print("💡 Or specify a project with --project-id")
            return 1
        
        if not current_project.get('enabled', True):
            print(f"⚠️  Project '{current_project['name']}' is disabled")
            return 1
        
        print(f"📂 Using project: {current_project['name']}")
        
        # Extract context
        project_root = args.project_root or current_project['path']
        extractor = TaskMasterContextExtractor(
            project_root=project_root
        )
        
        context = extractor.extract_project_context()
        
        if args.show_context:
            print("\n📝 Extracted Context:")
            print("=" * 50)
            for key, value in context.items():
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                print(f"{key}: {display_value}")
        
        # Generate variables for prompt
        variables = {
            'project_name': current_project['name'],
            'project_root': project_root,
            'prd_location': context.get('prd_location', 'Not found'),
            'requirements': context.get('requirements', 'Not found'),
            'success_criteria': context.get('success_criteria', 'Not found'),
            'current_task': context.get('current_task', 'No active task'),
            'git_branch': context.get('git_branch', 'unknown'),
            'git_status': context.get('git_status', 'No git repository'),
            'recent_changes': context.get('recent_changes', 'No recent changes'),
            'task_count': context.get('task_count', 0),
            'active_tasks': context.get('active_tasks', [])
        }
        
        # Get and render prompt
        if args.api:
            # Use API
            print(f"\n💡 Rendering prompt {args.prompt_id} via API...")
            try:
                response = requests.post(f"{args.api_url}/prompts/{args.prompt_id}/render", 
                                       json={'variables': variables})
                if response.status_code == 200:
                    result = response.json()
                    prompt_content = result['content']
                    prompt_title = result['title']
                else:
                    print(f"❌ API error: {response.status_code}")
                    return 1
            except Exception as e:
                print(f"❌ API request failed: {e}")
                return 1
        else:
            # Use direct access
            pm = PromptManager()
            prompt = pm.get_prompt(args.prompt_id)
            if not prompt:
                print(f"❌ Prompt with ID {args.prompt_id} not found")
                return 1
            
            prompt_title = prompt['title']
            prompt_content = prompt['content']
            
            # Replace variables
            for var, value in variables.items():
                prompt_content = prompt_content.replace(f"{{{var}}}", str(value))
        
        # Output result
        if args.dry_run:
            print(f"\n📋 Prompt: {prompt_title}")
            print("=" * 50)
            print(prompt_content)
        else:
            # Copy to clipboard
            if copy_to_clipboard(prompt_content):
                print(f"✅ Copied prompt '{prompt_title}' to clipboard!")
            else:
                print(f"📋 Prompt: {prompt_title}")
                print("=" * 50)
                print(prompt_content)
                print("\n⚠️  Clipboard not available - content displayed above")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n🐱 Meow! Interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())