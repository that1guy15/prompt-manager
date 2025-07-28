#!/usr/bin/env python3

"""
Prompt Manager CLI - Main entry point
Professional CLI interface with rich formatting and proper error handling
"""

import sys
import os
import argparse
from pathlib import Path

# Add package to path for development
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_manager.core import PromptManager, show_banner, get_api_url, show_help_content


def create_parser():
    """Create the main argument parser with all subcommands"""
    parser = argparse.ArgumentParser(
        prog="prompt-manager",
        description="🧶 AI Prompt Manager - Smart prompts for smarter workflows",
        epilog="For more help: prompt-manager help [topic]"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 1.0.0"
    )
    
    parser.add_argument(
        "--api-url", 
        default=os.environ.get("PROMPT_API_URL", "http://localhost:5000/api"), 
        help="API server URL (default: http://localhost:5000/api, or PROMPT_API_URL env var)"
    )
    
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the banner display"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Help command
    help_parser = subparsers.add_parser("help", help="Show interactive help")
    help_parser.add_argument(
        "topic", 
        nargs="?", 
        help="Help topic (quick-start, commands, task-master, browser, examples, troubleshooting)"
    )
    
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
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show banner for interactive commands (not for help)
    if not args.no_banner and args.command and args.command != "help":
        show_banner()
    
    if not args.command:
        if not args.no_banner:
            show_banner()
        parser.print_help()
        return 0
    
    try:
        # Get API URL with prompting if needed
        api_url = get_api_url(args.api_url)
        
        pm = PromptManager()
        
        if args.command == "help":
            show_help_content(args.topic)
            return 0
        
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
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n🐱 Meow! Interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())