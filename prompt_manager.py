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


def main():
    parser = argparse.ArgumentParser(description="AI Prompt Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
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
    
    if not args.command:
        parser.print_help()
        return
    
    pm = PromptManager()
    
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