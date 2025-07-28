#!/usr/bin/env python3

"""
Project Registry CLI - Manage Task-Master projects
Professional CLI for project management and configuration
"""

import sys
import argparse
from pathlib import Path

# Add package to path for development
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_manager.project_registry import ProjectRegistry


def show_registry_banner():
    """Display the project registry banner with cyan to violet gradient"""
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


def create_parser():
    """Create the argument parser for project-registry"""
    parser = argparse.ArgumentParser(
        prog="project-registry",
        description="🧶 Task-Master project registry management",
        epilog="Manage multiple Task-Master projects with ease"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 1.0.0"
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress the banner display'
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List projects
    list_parser = subparsers.add_parser("list", help="List all projects")
    list_parser.add_argument("--enabled-only", action="store_true", help="Show only enabled projects")
    
    # Add project
    add_parser = subparsers.add_parser("add", help="Add a new project")
    add_parser.add_argument("name", help="Project name")
    add_parser.add_argument("path", help="Project path")
    add_parser.add_argument("--task-master-dir", help="Task-Master directory (optional)")
    
    # Remove project
    remove_parser = subparsers.add_parser("remove", help="Remove a project")
    remove_parser.add_argument("project_id", help="Project ID to remove")
    
    # Enable/disable project
    enable_parser = subparsers.add_parser("enable", help="Enable a project")
    enable_parser.add_argument("project_id", help="Project ID to enable")
    
    disable_parser = subparsers.add_parser("disable", help="Disable a project")
    disable_parser.add_argument("project_id", help="Project ID to disable")
    
    # Discover projects
    subparsers.add_parser("discover", help="Auto-discover Task-Master projects")
    
    # Refresh project
    refresh_parser = subparsers.add_parser("refresh", help="Refresh a project's metadata")
    refresh_parser.add_argument("project_id", nargs="?", help="Project ID to refresh (optional)")
    
    # Show project details
    show_parser = subparsers.add_parser("show", help="Show project details")
    show_parser.add_argument("project_id", help="Project ID to show")
    
    return parser


def main():
    """Main project-registry CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show banner
    if not args.no_banner:
        show_registry_banner()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        registry = ProjectRegistry()
        
        if args.command == "list":
            projects = registry.list_projects()
            if args.enabled_only:
                projects = [p for p in projects if p.get('enabled', True)]
            
            if not projects:
                if args.enabled_only:
                    print("❌ No enabled projects found.")
                else:
                    print("❌ No projects found.")
                print("💡 Add projects with: project-registry add \"Project Name\" /path/to/project")
                return 1
            
            print(f"\n📂 {'Enabled Projects' if args.enabled_only else 'All Projects'}:")
            print("-" * 60)
            
            for project in projects:
                status = "✅" if project.get('enabled', True) else "❌"
                manually_added = "📝" if project.get('manually_added', False) else "🔍"
                
                print(f"{status} {manually_added} {project['name']} [{project['id']}]")
                print(f"   📁 Path: {project['path']}")
                if project.get('task_master_dir'):
                    print(f"   📋 Task-Master: {project['task_master_dir']}")
                if 'task_count' in project:
                    print(f"   📝 Tasks: {project['task_count']}")
                if project.get('git_info', {}).get('branch'):
                    print(f"   🌿 Branch: {project['git_info']['branch']}")
                print()
        
        elif args.command == "add":
            try:
                project_id = registry.add_project_manually(
                    args.name, 
                    args.path, 
                    args.task_master_dir
                )
                if project_id:
                    print(f"✅ Added project '{args.name}' with ID: {project_id}")
                else:
                    print("❌ Failed to add project")
                    return 1
            except Exception as e:
                print(f"❌ Error adding project: {e}")
                return 1
        
        elif args.command == "remove":
            try:
                success = registry.remove_project(args.project_id)
                if success:
                    print(f"✅ Removed project with ID: {args.project_id}")
                else:
                    print(f"❌ Project with ID '{args.project_id}' not found")
                    return 1
            except Exception as e:
                print(f"❌ Error removing project: {e}")
                return 1
        
        elif args.command == "enable":
            try:
                registry.toggle_project(args.project_id, enabled=True)
                print(f"✅ Enabled project with ID: {args.project_id}")
            except Exception as e:
                print(f"❌ Error enabling project: {e}")
                return 1
        
        elif args.command == "disable":
            try:
                registry.toggle_project(args.project_id, enabled=False)
                print(f"✅ Disabled project with ID: {args.project_id}")
            except Exception as e:
                print(f"❌ Error disabling project: {e}")
                return 1
        
        elif args.command == "discover":
            try:
                discovered = registry.discover_projects()
                if discovered:
                    print(f"✅ Discovered {len(discovered)} new projects:")
                    for project in discovered:
                        print(f"   📁 {project['name']} - {project['path']}")
                else:
                    print("💡 No new projects discovered")
            except Exception as e:
                print(f"❌ Error during discovery: {e}")
                return 1
        
        elif args.command == "refresh":
            try:
                if args.project_id:
                    registry.refresh_project(args.project_id)
                    print(f"✅ Refreshed project with ID: {args.project_id}")
                else:
                    registry.refresh_all_projects()
                    print("✅ Refreshed all projects")
            except Exception as e:
                print(f"❌ Error refreshing projects: {e}")
                return 1
        
        elif args.command == "show":
            try:
                project = registry.get_project(args.project_id)
                if not project:
                    print(f"❌ Project with ID '{args.project_id}' not found")
                    return 1
                
                print(f"\n📂 Project Details: {project['name']}")
                print("=" * 50)
                print(f"ID: {project['id']}")
                print(f"Path: {project['path']}")
                print(f"Enabled: {'✅ Yes' if project.get('enabled', True) else '❌ No'}")
                print(f"Manually Added: {'📝 Yes' if project.get('manually_added', False) else '🔍 Auto-discovered'}")
                
                if project.get('task_master_dir'):
                    print(f"Task-Master Dir: {project['task_master_dir']}")
                
                if 'task_count' in project:
                    print(f"Task Count: {project['task_count']}")
                
                if project.get('git_info'):
                    git_info = project['git_info']
                    print(f"Git Branch: {git_info.get('branch', 'unknown')}")
                    if git_info.get('status'):
                        print(f"Git Status: {git_info['status']}")
                
                if project.get('last_accessed'):
                    print(f"Last Accessed: {project['last_accessed']}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error showing project: {e}")
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n🐱 Meow! Interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())