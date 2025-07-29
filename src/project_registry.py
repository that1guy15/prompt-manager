#!/usr/bin/env python3

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import subprocess

class ProjectRegistry:
    """Manage multiple Task-Master projects and their contexts"""
    
    def __init__(self, registry_file: str = None):
        self.registry_file = registry_file or os.path.expanduser('~/.prompt_manager_projects.json')
        self.projects = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load project registry from file"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'projects': {},
            'current_project': None,
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_registry(self):
        """Save project registry to file"""
        self.projects['last_updated'] = datetime.now().isoformat()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        
        with open(self.registry_file, 'w') as f:
            json.dump(self.projects, f, indent=2)
    
    def discover_projects(self, search_paths: List[str] = None) -> List[Dict]:
        """Discover Task-Master projects in common locations"""
        if search_paths is None:
            search_paths = [
                # Skip home directory root - too broad
                os.path.expanduser('~/Projects'),
                os.path.expanduser('~/Code'),
                os.path.expanduser('~/workspace'),
                os.path.expanduser('~/work'),
                os.path.expanduser('~/Development'),
                os.path.expanduser('~/dev'),
                '/opt/projects',
                '/usr/local/projects'
            ]
        
        discovered = []
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            # Look for directories with task-master subdirectories or config files
            for root, dirs, files in os.walk(search_path):
                # Limit depth to avoid scanning too deep
                level = root.replace(search_path, '').count(os.sep)
                if level >= 3:
                    dirs[:] = []  # Don't recurse deeper
                    continue
                
                # Check for task-master indicators
                task_master_indicators = [
                    'task-master', '.task-master', 'tasks',
                    'task-master.yml', 'task-master.yaml', 'task-master.json',
                    '.taskmaster'
                ]
                
                found_indicators = []
                for indicator in task_master_indicators:
                    if indicator in dirs or indicator in files:
                        found_indicators.append(indicator)
                
                if found_indicators:
                    project_info = self._analyze_project(root, found_indicators)
                    if project_info:
                        discovered.append(project_info)
        
        return discovered
    
    def _analyze_project(self, project_path: str, indicators: List[str]) -> Optional[Dict]:
        """Analyze a potential project directory"""
        try:
            project_name = os.path.basename(project_path)
            
            # Get git info if available
            git_info = self._get_git_info(project_path)
            
            # Find task-master directory
            task_master_dir = None
            for indicator in indicators:
                potential_path = os.path.join(project_path, indicator)
                if os.path.exists(potential_path):
                    if os.path.isdir(potential_path):
                        task_master_dir = potential_path
                    else:
                        # Config file, use parent directory
                        task_master_dir = project_path
                    break
            
            # Count task files
            task_count = 0
            if task_master_dir and os.path.isdir(task_master_dir):
                task_count = len(list(Path(task_master_dir).rglob('*.md')))
            
            return {
                'id': self._generate_project_id(project_path),
                'name': project_name,
                'path': project_path,
                'task_master_dir': task_master_dir,
                'git_info': git_info,
                'task_count': task_count,
                'discovered_at': datetime.now().isoformat(),
                'last_used': None,
                'active': self._check_if_active(project_path)
            }
        
        except Exception as e:
            print(f"Error analyzing {project_path}: {e}")
            return None
    
    def _generate_project_id(self, project_path: str) -> str:
        """Generate unique project ID"""
        import hashlib
        return hashlib.md5(project_path.encode()).hexdigest()[:8]
    
    def _get_git_info(self, project_path: str) -> Dict:
        """Get git information for project"""
        git_info = {
            'is_git': False,
            'branch': None,
            'remote': None,
            'last_commit': None
        }
        
        try:
            # Check if git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  cwd=project_path, capture_output=True, text=True)
            if result.returncode == 0:
                git_info['is_git'] = True
                
                # Get branch
                result = subprocess.run(['git', 'branch', '--show-current'], 
                                      cwd=project_path, capture_output=True, text=True)
                if result.returncode == 0:
                    git_info['branch'] = result.stdout.strip()
                
                # Get remote
                result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                      cwd=project_path, capture_output=True, text=True)
                if result.returncode == 0:
                    git_info['remote'] = result.stdout.strip()
                
                # Get last commit
                result = subprocess.run(['git', 'log', '-1', '--format=%h %s'], 
                                      cwd=project_path, capture_output=True, text=True)
                if result.returncode == 0:
                    git_info['last_commit'] = result.stdout.strip()
        except:
            pass
        
        return git_info
    
    def _check_if_active(self, project_path: str) -> bool:
        """Check if project has recent activity"""
        try:
            # Check for recent file modifications
            recent_threshold = 7 * 24 * 60 * 60  # 7 days in seconds
            now = datetime.now().timestamp()
            
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith(('.md', '.py', '.js', '.ts', '.yml', '.yaml')):
                        file_path = os.path.join(root, file)
                        mtime = os.path.getmtime(file_path)
                        if now - mtime < recent_threshold:
                            return True
            
            return False
        except:
            return False
    
    def register_project(self, project_info: Dict) -> str:
        """Register a project in the registry"""
        project_id = project_info['id']
        self.projects['projects'][project_id] = project_info
        self._save_registry()
        return project_id
    
    def register_projects(self, projects: List[Dict]) -> List[str]:
        """Register multiple projects"""
        project_ids = []
        for project in projects:
            project_id = self.register_project(project)
            project_ids.append(project_id)
        return project_ids
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        return self.projects['projects'].get(project_id)
    
    def get_project_by_path(self, path: str) -> Optional[Dict]:
        """Get project by path"""
        for project in self.projects['projects'].values():
            if project['path'] == path:
                return project
        return None
    
    def list_projects(self, active_only: bool = False) -> List[Dict]:
        """List all registered projects"""
        projects = list(self.projects['projects'].values())
        
        if active_only:
            projects = [p for p in projects if p.get('active', False)]
        
        # Sort by last used, then by name
        return sorted(projects, key=lambda p: (
            p.get('last_used') or '1970-01-01',
            p['name']
        ), reverse=True)
    
    def set_current_project(self, project_id: str) -> bool:
        """Set the current active project"""
        if project_id in self.projects['projects']:
            self.projects['current_project'] = project_id
            self.projects['projects'][project_id]['last_used'] = datetime.now().isoformat()
            self._save_registry()
            return True
        return False
    
    def get_current_project(self) -> Optional[Dict]:
        """Get the current active project"""
        current_id = self.projects.get('current_project')
        if current_id:
            return self.get_project(current_id)
        return None
    
    def auto_detect_current_project(self, cwd: str = None) -> Optional[Dict]:
        """Auto-detect current project based on working directory"""
        if cwd is None:
            cwd = os.getcwd()
        
        # First, check if we're directly in a registered project
        project = self.get_project_by_path(cwd)
        if project:
            self.set_current_project(project['id'])
            return project
        
        # Then, check if we're in a subdirectory of a registered project
        for project in self.projects['projects'].values():
            if cwd.startswith(project['path']):
                self.set_current_project(project['id'])
                return project
        
        # Finally, try to discover a new project in the current directory
        current_project_info = self._analyze_project(cwd, [
            'task-master', '.task-master', 'tasks',
            'task-master.yml', 'task-master.yaml', 'task-master.json'
        ])
        
        if current_project_info:
            project_id = self.register_project(current_project_info)
            self.set_current_project(project_id)
            return current_project_info
        
        return None
    
    def get_project_context(self, project_id: str = None) -> Optional[Tuple[Dict, Dict]]:
        """Get project context for prompt generation"""
        if project_id is None:
            project = self.get_current_project()
        else:
            project = self.get_project(project_id)
        
        if not project:
            return None
        
        # Import here to avoid circular imports
        from task_master_context_extractor import TaskMasterContextExtractor
        
        try:
            extractor = TaskMasterContextExtractor(project['path'])
            context, variables = extractor.get_context_for_prompt()
            
            # Add project registry info to context
            context['registry_info'] = {
                'project_id': project['id'],
                'project_name': project['name'],
                'task_count': project['task_count'],
                'git_info': project['git_info']
            }
            
            return context, variables
        except Exception as e:
            print(f"Error extracting context for project {project['name']}: {e}")
            return None
    
    def remove_project(self, project_id: str) -> bool:
        """Remove a project from registry"""
        if project_id in self.projects['projects']:
            del self.projects['projects'][project_id]
            
            # Clear current project if it was the removed one
            if self.projects.get('current_project') == project_id:
                self.projects['current_project'] = None
            
            self._save_registry()
            return True
        return False
    
    def add_project_manually(self, name: str, path: str, task_master_dir: str = None) -> Optional[str]:
        """Manually add a project to the registry"""
        # Validate path exists
        if not os.path.exists(path):
            raise ValueError(f"Project path does not exist: {path}")
        
        # Convert to absolute path
        path = os.path.abspath(path)
        
        # Check if project already exists
        existing = self.get_project_by_path(path)
        if existing:
            raise ValueError(f"Project already exists: {existing['name']} [{existing['id']}]")
        
        # Auto-detect task-master directory if not provided
        if task_master_dir is None:
            indicators = ['task-master', '.task-master', 'tasks']
            for indicator in indicators:
                potential_path = os.path.join(path, indicator)
                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    task_master_dir = potential_path
                    break
            
            # If still not found, check for config files
            if task_master_dir is None:
                config_files = ['task-master.yml', 'task-master.yaml', 'task-master.json']
                for config_file in config_files:
                    config_path = os.path.join(path, config_file)
                    if os.path.exists(config_path):
                        task_master_dir = path
                        break
        
        if task_master_dir and not os.path.exists(task_master_dir):
            raise ValueError(f"Task-Master directory does not exist: {task_master_dir}")
        
        # Create project info
        project_info = {
            'id': self._generate_project_id(path),
            'name': name,
            'path': path,
            'task_master_dir': task_master_dir,
            'git_info': self._get_git_info(path),
            'task_count': 0,
            'discovered_at': datetime.now().isoformat(),
            'last_used': None,
            'active': self._check_if_active(path),
            'manually_added': True,
            'enabled': True
        }
        
        # Count task files if task-master directory exists
        if task_master_dir and os.path.isdir(task_master_dir):
            project_info['task_count'] = len(list(Path(task_master_dir).rglob('*.md')))
        
        # Register the project
        project_id = self.register_project(project_info)
        return project_id
    
    def enable_project(self, project_id: str) -> bool:
        """Enable a project (show in listings)"""
        if project_id in self.projects['projects']:
            self.projects['projects'][project_id]['enabled'] = True
            self._save_registry()
            return True
        return False
    
    def disable_project(self, project_id: str) -> bool:
        """Disable a project (hide from listings but keep in registry)"""
        if project_id in self.projects['projects']:
            self.projects['projects'][project_id]['enabled'] = False
            
            # Clear current project if it was the disabled one
            if self.projects.get('current_project') == project_id:
                self.projects['current_project'] = None
            
            self._save_registry()
            return True
        return False
    
    def list_projects(self, active_only: bool = False, enabled_only: bool = True) -> List[Dict]:
        """List all registered projects"""
        projects = list(self.projects['projects'].values())
        
        if enabled_only:
            projects = [p for p in projects if p.get('enabled', True)]
        
        if active_only:
            projects = [p for p in projects if p.get('active', False)]
        
        # Sort by last used, then by name
        return sorted(projects, key=lambda p: (
            p.get('last_used') or '1970-01-01',
            p['name']
        ), reverse=True)
    
    def update_project(self, project_id: str, **updates) -> bool:
        """Update project information"""
        if project_id not in self.projects['projects']:
            return False
        
        allowed_updates = ['name', 'path', 'task_master_dir', 'enabled']
        
        for key, value in updates.items():
            if key in allowed_updates:
                if key == 'path' and not os.path.exists(value):
                    raise ValueError(f"Path does not exist: {value}")
                if key == 'task_master_dir' and value and not os.path.exists(value):
                    raise ValueError(f"Task-Master directory does not exist: {value}")
                
                self.projects['projects'][project_id][key] = value
        
        self._save_registry()
        return True
    
    def get_project_settings(self) -> Dict:
        """Get project registry settings"""
        return {
            'total_projects': len(self.projects['projects']),
            'enabled_projects': len([p for p in self.projects['projects'].values() if p.get('enabled', True)]),
            'current_project': self.projects.get('current_project'),
            'auto_discovery_enabled': self.projects.get('auto_discovery_enabled', True),
            'last_discovery': self.projects.get('last_discovery'),
            'registry_file': self.registry_file
        }
    
    def update_settings(self, **settings) -> bool:
        """Update registry settings"""
        allowed_settings = ['auto_discovery_enabled']
        
        for key, value in settings.items():
            if key in allowed_settings:
                self.projects[key] = value
        
        self._save_registry()
        return True
    
    def refresh_project(self, project_id: str) -> bool:
        """Refresh project information"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        # Re-analyze the project
        updated_info = self._analyze_project(project['path'], [
            'task-master', '.task-master', 'tasks',
            'task-master.yml', 'task-master.yaml', 'task-master.json'
        ])
        
        if updated_info:
            # Preserve registry-specific fields
            updated_info['id'] = project['id']
            updated_info['last_used'] = project.get('last_used')
            updated_info['discovered_at'] = project.get('discovered_at')
            
            self.projects['projects'][project_id] = updated_info
            self._save_registry()
            return True
        
        return False


def main():
    """CLI interface for project registry management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Task-Master project registry")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover Task-Master projects')
    discover_parser.add_argument('--paths', nargs='+', help='Paths to search')
    discover_parser.add_argument('--register', action='store_true', help='Register discovered projects')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List registered projects')
    list_parser.add_argument('--active', action='store_true', help='Show only active projects')
    list_parser.add_argument('--all', action='store_true', help='Show all projects (including disabled)')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Manually add a project')
    add_parser.add_argument('name', help='Project name')
    add_parser.add_argument('path', help='Project directory path')
    add_parser.add_argument('--task-master-dir', help='Task-Master directory (auto-detected if not provided)')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a project')
    remove_parser.add_argument('project_id', help='Project ID to remove')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable a project')
    enable_parser.add_argument('project_id', help='Project ID to enable')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable a project')
    disable_parser.add_argument('project_id', help='Project ID to disable')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update project information')
    update_parser.add_argument('project_id', help='Project ID to update')
    update_parser.add_argument('--name', help='New project name')
    update_parser.add_argument('--path', help='New project path')
    update_parser.add_argument('--task-master-dir', help='New Task-Master directory')
    
    # Current command
    current_parser = subparsers.add_parser('current', help='Show/set current project')
    current_parser.add_argument('project_id', nargs='?', help='Project ID to set as current')
    
    # Auto command
    subparsers.add_parser('auto', help='Auto-detect current project')
    
    # Context command
    context_parser = subparsers.add_parser('context', help='Show project context')
    context_parser.add_argument('project_id', nargs='?', help='Project ID (default: current)')
    
    # Settings command
    settings_parser = subparsers.add_parser('settings', help='Manage registry settings')
    settings_parser.add_argument('--auto-discovery', choices=['on', 'off'], help='Enable/disable auto-discovery')
    settings_parser.add_argument('--show', action='store_true', help='Show current settings')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    registry = ProjectRegistry()
    
    if args.command == 'discover':
        print("🔍 Discovering Task-Master projects...")
        projects = registry.discover_projects(args.paths)
        
        if not projects:
            print("No Task-Master projects found.")
            return
        
        print(f"Found {len(projects)} projects:")
        for project in projects:
            print(f"  📂 {project['name']} ({project['path']})")
            print(f"     Task files: {project['task_count']}")
            if project['git_info']['is_git']:
                print(f"     Git: {project['git_info']['branch']} - {project['git_info']['last_commit']}")
        
        if args.register:
            project_ids = registry.register_projects(projects)
            print(f"\n✅ Registered {len(project_ids)} projects")
    
    elif args.command == 'add':
        try:
            project_id = registry.add_project_manually(
                args.name, 
                args.path, 
                args.task_master_dir
            )
            project = registry.get_project(project_id)
            print(f"✅ Added project: {project['name']} [{project_id[:8]}]")
            print(f"   Path: {project['path']}")
            if project['task_master_dir']:
                print(f"   Task-Master: {project['task_master_dir']}")
                print(f"   Task files: {project['task_count']}")
        except Exception as e:
            print(f"❌ Failed to add project: {e}")
    
    elif args.command == 'remove':
        project = registry.get_project(args.project_id)
        if project:
            if registry.remove_project(args.project_id):
                print(f"✅ Removed project: {project['name']}")
            else:
                print(f"❌ Failed to remove project")
        else:
            print(f"❌ Project {args.project_id} not found")
    
    elif args.command == 'enable':
        project = registry.get_project(args.project_id)
        if project:
            if registry.enable_project(args.project_id):
                print(f"✅ Enabled project: {project['name']}")
            else:
                print(f"❌ Failed to enable project")
        else:
            print(f"❌ Project {args.project_id} not found")
    
    elif args.command == 'disable':
        project = registry.get_project(args.project_id)
        if project:
            if registry.disable_project(args.project_id):
                print(f"✅ Disabled project: {project['name']}")
            else:
                print(f"❌ Failed to disable project")
        else:
            print(f"❌ Project {args.project_id} not found")
    
    elif args.command == 'update':
        updates = {}
        if args.name:
            updates['name'] = args.name
        if args.path:
            updates['path'] = args.path
        if args.task_master_dir:
            updates['task_master_dir'] = args.task_master_dir
        
        if not updates:
            print("❌ No updates provided")
            return
        
        try:
            if registry.update_project(args.project_id, **updates):
                project = registry.get_project(args.project_id)
                print(f"✅ Updated project: {project['name']}")
                for key, value in updates.items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ Project {args.project_id} not found")
        except Exception as e:
            print(f"❌ Failed to update project: {e}")

    elif args.command == 'list':
        projects = registry.list_projects(
            active_only=args.active, 
            enabled_only=not args.all
        )
        
        if not projects:
            print("No projects found. Run 'discover --register' or 'add' to add projects.")
            return
        
        current_id = registry.projects.get('current_project')
        
        status_filter = ""
        if args.active:
            status_filter = " (active only)"
        elif args.all:
            status_filter = " (including disabled)"
        
        print(f"📋 Projects{status_filter} ({len(projects)}):")
        for project in projects:
            current_marker = "👉 " if project['id'] == current_id else "   "
            active_marker = "🟢" if project.get('active') else "⚫"
            enabled_marker = "" if project.get('enabled', True) else " [DISABLED]"
            manual_marker = " [MANUAL]" if project.get('manually_added') else ""
            
            print(f"{current_marker}{active_marker} {project['name']} [{project['id'][:8]}]{enabled_marker}{manual_marker}")
            print(f"      {project['path']}")
            if project.get('task_master_dir'):
                print(f"      Task-Master: {project['task_master_dir']} ({project['task_count']} tasks)")
            if project.get('last_used'):
                print(f"      Last used: {project['last_used']}")
            if project.get('git_info', {}).get('branch'):
                print(f"      Git: {project['git_info']['branch']}")
    
    elif args.command == 'current':
        if args.project_id:
            if registry.set_current_project(args.project_id):
                project = registry.get_project(args.project_id)
                print(f"✅ Set current project: {project['name']}")
            else:
                print(f"❌ Project {args.project_id} not found")
        else:
            current = registry.get_current_project()
            if current:
                print(f"Current project: {current['name']} [{current['id']}]")
                print(f"Path: {current['path']}")
            else:
                print("No current project set")
    
    elif args.command == 'auto':
        project = registry.auto_detect_current_project()
        if project:
            print(f"✅ Detected project: {project['name']}")
            print(f"Path: {project['path']}")
        else:
            print("❌ No Task-Master project detected in current directory")
    
    elif args.command == 'context':
        result = registry.get_project_context(args.project_id)
        if result:
            context, variables = result
            print("📊 Project Context:")
            print(json.dumps(context, indent=2))
            print("\n📝 Variables:")
            for key, value in variables.items():
                print(f"{key}: {value}")
        else:
            print("❌ Unable to get project context")
    
    elif args.command == 'settings':
        if args.show:
            settings = registry.get_project_settings()
            print("⚙️ Project Registry Settings:")
            print(f"   Total projects: {settings['total_projects']}")
            print(f"   Enabled projects: {settings['enabled_projects']}")
            print(f"   Current project: {settings['current_project'] or 'None'}")
            print(f"   Auto-discovery: {'Enabled' if settings.get('auto_discovery_enabled', True) else 'Disabled'}")
            print(f"   Registry file: {settings['registry_file']}")
            if settings.get('last_discovery'):
                print(f"   Last discovery: {settings['last_discovery']}")
        else:
            updates = {}
            if args.auto_discovery:
                updates['auto_discovery_enabled'] = args.auto_discovery == 'on'
            
            if updates:
                registry.update_settings(**updates)
                print("✅ Settings updated")
                for key, value in updates.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ No settings to update")


if __name__ == "__main__":
    main()