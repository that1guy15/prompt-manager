#!/usr/bin/env python3

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

class TaskMasterContextExtractor:
    """Extract project context and variables from Task-Master files"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or self._find_project_root()
        self.task_master_dir = self._find_task_master_dir()
        self.context_cache = {}
    
    def _find_project_root(self) -> str:
        """Find project root by looking for .git directory"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return str(current)
            current = current.parent
        return str(Path.cwd())
    
    def _find_task_master_dir(self) -> Optional[Path]:
        """Find Task-Master directory in project"""
        root = Path(self.project_root)
        
        # Skip if we're in home directory or root
        home = Path.home()
        if root == home or root == Path('/'):
            return None
            
        # Common Task-Master locations
        possible_paths = [
            root / 'task-master',
            root / '.task-master',
            root / 'tasks',
            root / 'project' / 'tasks',
            root / 'docs' / 'task-master'
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path
        
        # Search for task-master config files (limit depth to avoid scanning entire filesystem)
        max_depth = 3  # Only search 3 levels deep
        for config_file in ['task-master.yml', 'task-master.yaml', 'task-master.json', '.taskmaster']:
            for depth in range(max_depth + 1):
                pattern = '/'.join(['*'] * depth) + '/' + config_file
                try:
                    found = list(root.glob(pattern))
                    if found:
                        return found[0].parent
                except:
                    # Skip if permission denied or other errors
                    pass
        
        return None
    
    def extract_project_context(self) -> Dict[str, any]:
        """Extract comprehensive project context from Task-Master and project files"""
        context = {
            'project_root': self.project_root,
            'project_name': Path(self.project_root).name,
            'git_branch': self._get_git_branch(),
            'active_task': None,
            'prd_location': None,
            'feature_docs': None,
            'requirements': [],
            'success_criteria': [],
            'custom_context': {},
            'task_status': None
        }
        
        if self.task_master_dir:
            # Extract from Task-Master files
            context.update(self._extract_from_task_files())
            
            # Find active task
            active_task = self._find_active_task()
            if active_task:
                context['active_task'] = active_task
                context.update(self._extract_task_details(active_task))
        
        # Extract from project files
        context.update(self._extract_from_project_files())
        
        return context
    
    def _extract_from_task_files(self) -> Dict:
        """Extract context from Task-Master configuration and task files"""
        extracted = {}
        
        # Look for task-master config
        config_files = ['task-master.yml', 'task-master.yaml', 'task-master.json']
        for config_file in config_files:
            config_path = self.task_master_dir / config_file
            if config_path.exists():
                if config_file.endswith('.json'):
                    with open(config_path) as f:
                        config = json.load(f)
                else:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                
                # Extract relevant fields
                if 'prd_location' in config:
                    extracted['prd_location'] = config['prd_location']
                if 'docs_directory' in config:
                    extracted['feature_docs'] = config['docs_directory']
                if 'project' in config:
                    extracted['custom_context'].update(config['project'])
                break
        
        # Look for PRD files
        prd_files = list(self.task_master_dir.rglob('*PRD*.md'))
        if prd_files and not extracted.get('prd_location'):
            extracted['prd_location'] = str(prd_files[0])
        
        # Look for docs directory
        docs_dirs = [d for d in self.task_master_dir.iterdir() 
                     if d.is_dir() and d.name.lower() in ['docs', 'documentation', 'doc']]
        if docs_dirs and not extracted.get('feature_docs'):
            extracted['feature_docs'] = str(docs_dirs[0])
        
        return extracted
    
    def _find_active_task(self) -> Optional[Path]:
        """Find the currently active task file"""
        if not self.task_master_dir:
            return None
        
        # Look for active tasks directory
        active_dir = self.task_master_dir / 'active'
        if active_dir.exists():
            task_files = list(active_dir.glob('*.md'))
            if task_files:
                # Return most recently modified
                return max(task_files, key=lambda f: f.stat().st_mtime)
        
        # Look for task files with status markers
        for task_file in self.task_master_dir.rglob('*.md'):
            content = task_file.read_text()
            if re.search(r'status:\s*(active|in[- ]progress|current)', content, re.IGNORECASE):
                return task_file
        
        return None
    
    def _extract_task_details(self, task_file: Path) -> Dict:
        """Extract details from a specific task file"""
        content = task_file.read_text()
        details = {}
        
        # Extract various patterns
        patterns = {
            'prd_location': [
                r'PRD:\s*(.+)$',
                r'PRD Location:\s*(.+)$',
                r'Product Requirements:\s*(.+)$'
            ],
            'feature_docs': [
                r'DOCS:\s*(.+)$',
                r'Documentation:\s*(.+)$',
                r'Docs Directory:\s*(.+)$'
            ],
            'task_status': [
                r'Status:\s*(.+)$',
                r'Current Status:\s*(.+)$'
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    details[field] = match.group(1).strip()
                    break
        
        # Extract requirements section
        req_match = re.search(
            r'(?:Requirements?|Key Requirements?):\s*\n((?:[-*]\s*.+\n?)+)',
            content, re.MULTILINE | re.IGNORECASE
        )
        if req_match:
            requirements = [
                line.strip().lstrip('-*').strip() 
                for line in req_match.group(1).strip().split('\n')
            ]
            details['requirements'] = requirements
        
        # Extract success criteria
        success_match = re.search(
            r'(?:Success Criteria|Critical Success Criteria):\s*\n((?:[-*]\s*.+\n?)+)',
            content, re.MULTILINE | re.IGNORECASE
        )
        if success_match:
            criteria = [
                line.strip().lstrip('-*').strip() 
                for line in success_match.group(1).strip().split('\n')
            ]
            details['success_criteria'] = criteria
        
        return details
    
    def _extract_from_project_files(self) -> Dict:
        """Extract additional context from project files"""
        extracted = {}
        
        # Check for README with project info
        readme_path = Path(self.project_root) / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()
            # Extract project description
            desc_match = re.search(r'^#\s+.+\n\n(.+?)(?:\n\n|$)', content, re.MULTILINE)
            if desc_match:
                extracted['project_description'] = desc_match.group(1).strip()
        
        # Check for package.json (Node projects)
        package_json = Path(self.project_root) / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                package = json.load(f)
                if 'description' in package:
                    extracted['project_description'] = package['description']
        
        return extracted
    
    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def format_for_prompt(self, context: Dict) -> Dict[str, str]:
        """Format extracted context for prompt variables"""
        variables = {}
        
        # Map context to prompt variables
        if context.get('prd_location'):
            variables['PRD_LOCATION'] = context['prd_location']
        
        if context.get('feature_docs'):
            variables['FEATURE_DOCS'] = context['feature_docs']
        
        if context.get('requirements'):
            variables['PROJECT_REQUIRMENTS'] = '\n'.join(
                f"{i+1}. {req}" for i, req in enumerate(context['requirements'])
            )
        
        if context.get('success_criteria'):
            variables['PROJECT_SUCCESS_CRITERIA'] = '\n- '.join(
                [''] + context['success_criteria']
            )[1:]  # Remove leading newline
        
        # Build custom prompt from context
        custom_parts = []
        if context.get('active_task'):
            custom_parts.append(f"Working on: {context['active_task'].name}")
        if context.get('task_status'):
            custom_parts.append(f"Task Status: {context['task_status']}")
        if context.get('git_branch'):
            custom_parts.append(f"Branch: {context['git_branch']}")
        
        if custom_parts:
            variables['CUSTOM_PROMPT'] = '\n'.join(custom_parts)
        
        return variables
    
    def get_context_for_prompt(self, prompt_id: int = 4) -> Tuple[Dict, Dict]:
        """Get full context and formatted variables for a specific prompt"""
        context = self.extract_project_context()
        variables = self.format_for_prompt(context)
        
        return context, variables


def main():
    """CLI interface for testing context extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Task-Master context")
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--format', choices=['json', 'variables'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    extractor = TaskMasterContextExtractor(args.project_root)
    context = extractor.extract_project_context()
    
    if args.format == 'json':
        print(json.dumps(context, indent=2))
    else:
        variables = extractor.format_for_prompt(context)
        for key, value in variables.items():
            print(f"{key}={value}")
            print()


if __name__ == "__main__":
    main()