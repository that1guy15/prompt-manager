#!/usr/bin/env python3

import os
import sys
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt_manager import PromptManager
from task_master_context_extractor import TaskMasterContextExtractor

class TaskMasterPlugin:
    def __init__(self, api_url: str = "http://localhost:5000/api"):
        self.api_url = api_url
        self.pm = PromptManager()
        self.task_master_dir = os.environ.get('TASK_MASTER_DIR', '/path/to/task-master')
        self.context_extractor = TaskMasterContextExtractor()
    
    def analyze_task_context(self, task_file: str) -> Dict:
        """Analyze a task file to determine context for prompt selection"""
        context = {
            'task_type': '',
            'technologies': [],
            'is_bug_fix': False,
            'is_feature': False,
            'is_planning': False,
            'requires_testing': False,
            'current_phase': ''
        }
        
        try:
            with open(task_file, 'r') as f:
                content = f.read().lower()
            
            # Detect task type
            if 'bug' in content or 'fix' in content or 'error' in content:
                context['is_bug_fix'] = True
                context['task_type'] = 'debugging'
            
            if 'feature' in content or 'implement' in content:
                context['is_feature'] = True
                context['task_type'] = 'development'
            
            if 'design' in content or 'architecture' in content or 'plan' in content:
                context['is_planning'] = True
                context['task_type'] = 'planning'
            
            if 'test' in content or 'testing' in content:
                context['requires_testing'] = True
            
            # Detect technologies
            tech_patterns = {
                'python': r'\b(python|django|flask|fastapi)\b',
                'javascript': r'\b(javascript|js|node|react|vue|angular)\b',
                'typescript': r'\b(typescript|ts)\b',
                'api': r'\b(api|rest|graphql|endpoint)\b',
                'database': r'\b(database|sql|postgres|mysql|mongodb)\b'
            }
            
            for tech, pattern in tech_patterns.items():
                if re.search(pattern, content):
                    context['technologies'].append(tech)
            
            # Detect current phase
            if 'todo' in content or 'pending' in content:
                context['current_phase'] = 'planning'
            elif 'in progress' in content or 'implementing' in content:
                context['current_phase'] = 'development'
            elif 'review' in content or 'testing' in content:
                context['current_phase'] = 'review'
            
        except Exception as e:
            print(f"Error analyzing task file: {e}")
        
        return context
    
    def get_prompt_for_task(self, task_context: Dict) -> Optional[Dict]:
        """Select the most appropriate prompt based on task context"""
        
        # First, try to get suggestions from the API
        try:
            response = requests.post(f"{self.api_url}/prompts/suggest", json={
                'context': {
                    'current_task': task_context.get('task_type', ''),
                    'has_error': task_context.get('is_bug_fix', False),
                    'is_planning': task_context.get('is_planning', False)
                }
            })
            
            if response.status_code == 200:
                suggestions = response.json()
                if suggestions:
                    return suggestions[0]  # Return the top suggestion
        except Exception as e:
            print(f"Error getting prompt suggestions: {e}")
        
        # Fallback to local selection
        prompts = self.pm.prompts["prompts"]
        
        # Filter by task type
        if task_context['is_bug_fix']:
            prompts = [p for p in prompts if p['category'] == 'debugging']
        elif task_context['is_planning']:
            prompts = [p for p in prompts if p['category'] == 'planning']
        elif task_context['is_feature']:
            prompts = [p for p in prompts if p['category'] == 'development']
        
        # Sort by usage count
        prompts = sorted(prompts, key=lambda x: x['used_count'], reverse=True)
        
        return prompts[0] if prompts else None
    
    def inject_prompt_into_workflow(self, task_file: str = None, variables: Dict[str, str] = None) -> Tuple[bool, str]:
        """Automatically inject the appropriate prompt for a task"""
        
        # If no task file provided, use context extractor to find active task
        if task_file is None:
            context_data, auto_variables = self.context_extractor.get_context_for_prompt()
            context = self._convert_context_for_analysis(context_data)
        else:
            # Analyze the specific task file
            context = self.analyze_task_context(task_file)
            auto_variables = self.extract_variables_from_task(task_file)
        
        # Get the best prompt
        prompt = self.get_prompt_for_task(context)
        if not prompt:
            # Default to Task Master prompt if available
            prompt = self.pm.get_prompt(4)  # Task Master Project Continuation
            if not prompt:
                return False, "No suitable prompt found for this task"
        
        # Merge provided variables with auto-extracted ones
        if variables is None:
            variables = auto_variables
        else:
            # User-provided variables take precedence
            auto_variables.update(variables)
            variables = auto_variables
        
        # Render the prompt
        try:
            response = requests.post(f"{self.api_url}/prompts/{prompt['id']}/render", json={
                'variables': variables
            })
            
            if response.status_code == 200:
                result = response.json()
                return True, result['content']
            else:
                error_msg = response.json().get('error', 'Unknown error')
                missing_vars = response.json().get('missing', [])
                if missing_vars:
                    return False, f"Missing variables: {', '.join(missing_vars)}\nExtracted: {list(variables.keys())}"
                return False, f"Error rendering prompt: {error_msg}"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _convert_context_for_analysis(self, context_data: Dict) -> Dict:
        """Convert context extractor format to analysis format"""
        return {
            'task_type': 'project-management' if context_data.get('active_task') else 'development',
            'technologies': [],
            'is_bug_fix': 'bug' in context_data.get('git_branch', '').lower(),
            'is_feature': 'feature' in context_data.get('git_branch', '').lower(),
            'is_planning': bool(context_data.get('prd_location')),
            'requires_testing': False,
            'current_phase': context_data.get('task_status', 'development')
        }
    
    def extract_variables_from_task(self, task_file: str) -> Dict[str, str]:
        """Extract common variables from task file"""
        variables = {}
        
        try:
            with open(task_file, 'r') as f:
                content = f.read()
            
            # Extract PRD location
            prd_match = re.search(r'PRD:\s*(.+)$', content, re.MULTILINE)
            if prd_match:
                variables['PRD_LOCATION'] = prd_match.group(1).strip()
            
            # Extract feature docs
            docs_match = re.search(r'DOCS:\s*(.+)$', content, re.MULTILINE)
            if docs_match:
                variables['FEATURE_DOCS'] = docs_match.group(1).strip()
            
            # Extract requirements
            req_section = re.search(r'REQUIREMENTS:(.*?)(?=\n\n|\Z)', content, re.DOTALL)
            if req_section:
                variables['PROJECT_REQUIRMENTS'] = req_section.group(1).strip()
            
            # Extract success criteria
            success_section = re.search(r'SUCCESS CRITERIA:(.*?)(?=\n\n|\Z)', content, re.DOTALL)
            if success_section:
                variables['PROJECT_SUCCESS_CRITERIA'] = success_section.group(1).strip()
            
        except Exception as e:
            print(f"Error extracting variables: {e}")
        
        return variables
    
    def monitor_active_tasks(self):
        """Monitor active tasks and suggest prompts"""
        active_tasks_dir = os.path.join(self.task_master_dir, 'active_tasks')
        
        if not os.path.exists(active_tasks_dir):
            print(f"Active tasks directory not found: {active_tasks_dir}")
            return
        
        for task_file in Path(active_tasks_dir).glob('*.md'):
            print(f"\nAnalyzing task: {task_file.name}")
            context = self.analyze_task_context(str(task_file))
            prompt = self.get_prompt_for_task(context)
            
            if prompt:
                print(f"  Recommended prompt: {prompt['title']} (ID: {prompt['id']})")
                print(f"  Category: {prompt['category']}")
                print(f"  Usage count: {prompt['used_count']}")
                print(f"  Confidence: {self._calculate_confidence(context, prompt):.1%}")
            else:
                print("  No suitable prompt found")
    
    def auto_inject_for_active_task(self, task_name: str = None) -> Tuple[bool, str]:
        """Automatically inject prompt for the most recent or specified active task"""
        active_tasks_dir = os.path.join(self.task_master_dir, 'active_tasks')
        
        if not os.path.exists(active_tasks_dir):
            return False, f"Active tasks directory not found: {active_tasks_dir}"
        
        # Find the target task file
        task_files = list(Path(active_tasks_dir).glob('*.md'))
        if not task_files:
            return False, "No active tasks found"
        
        if task_name:
            # Find specific task
            target_file = None
            for f in task_files:
                if task_name.lower() in f.name.lower():
                    target_file = f
                    break
            if not target_file:
                return False, f"Task '{task_name}' not found"
        else:
            # Use most recent task
            target_file = max(task_files, key=lambda f: f.stat().st_mtime)
        
        return self.inject_prompt_into_workflow(str(target_file))
    
    def watch_task_changes(self, callback=None):
        """Watch for changes in task files and auto-suggest prompts"""
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            print("Install watchdog: pip install watchdog")
            return
        
        class TaskChangeHandler(FileSystemEventHandler):
            def __init__(self, plugin):
                self.plugin = plugin
                
            def on_modified(self, event):
                if event.src_path.endswith('.md') and 'active_tasks' in event.src_path:
                    print(f"\n📝 Task updated: {Path(event.src_path).name}")
                    context = self.plugin.analyze_task_context(event.src_path)
                    prompt = self.plugin.get_prompt_for_task(context)
                    
                    if prompt:
                        print(f"💡 Suggested prompt: {prompt['title']} (ID: {prompt['id']})")
                        if callback:
                            callback(prompt, context)
        
        observer = Observer()
        observer.schedule(TaskChangeHandler(self), self.task_master_dir, recursive=True)
        observer.start()
        print(f"👀 Watching {self.task_master_dir} for task changes...")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    
    def _calculate_confidence(self, context: Dict, prompt: Dict) -> float:
        """Calculate confidence score for prompt recommendation"""
        score = 0.0
        
        # Category match (40% weight)
        if context.get('task_type') == prompt.get('category'):
            score += 0.4
        
        # Technology overlap (30% weight)
        prompt_tags = set(prompt.get('tags', []))
        context_techs = set(context.get('technologies', []))
        if prompt_tags & context_techs:
            score += 0.3 * (len(prompt_tags & context_techs) / len(prompt_tags | context_techs))
        
        # Usage frequency (20% weight)
        if prompt.get('used_count', 0) > 0:
            score += min(0.2, prompt['used_count'] / 10.0)
        
        # Phase match (10% weight)  
        if context.get('current_phase') in prompt.get('content', '').lower():
            score += 0.1
        
        return score
    
    def create_task_prompt_mapping(self):
        """Create a mapping file for task types to prompts"""
        mapping = {
            'bug_fix': {
                'prompt_ids': [2],  # Bug Analysis prompt
                'auto_variables': {
                    'environment': 'production'
                }
            },
            'feature_development': {
                'prompt_ids': [3, 4],  # Feature Design, Task Master
                'auto_variables': {}
            },
            'code_review': {
                'prompt_ids': [1],  # Code Review Request
                'auto_variables': {
                    'context': 'Pull request review'
                }
            },
            'api_testing': {
                'prompt_ids': [5],  # API Test Request
                'auto_variables': {
                    'method': 'GET'
                }
            }
        }
        
        with open('task_prompt_mapping.json', 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print("Created task_prompt_mapping.json")

def main():
    plugin = TaskMasterPlugin()
    
    if len(sys.argv) < 2:
        print("Usage: task_master_plugin.py <command> [args]")
        print("Commands:")
        print("  analyze <task_file>     - Analyze a task file")
        print("  inject <task_file>      - Inject prompt for a task")
        print("  auto-inject [task_name] - Auto-inject for active task")
        print("  monitor                 - Monitor active tasks")
        print("  watch                   - Watch for task changes")
        print("  create-mapping          - Create task-prompt mapping")
        return
    
    command = sys.argv[1]
    
    if command == 'analyze' and len(sys.argv) > 2:
        context = plugin.analyze_task_context(sys.argv[2])
        print(json.dumps(context, indent=2))
    
    elif command == 'inject' and len(sys.argv) > 2:
        success, content = plugin.inject_prompt_into_workflow(sys.argv[2])
        if success:
            print("Prompt injected successfully:")
            print("-" * 40)
            print(content)
        else:
            print(f"Failed: {content}")
    
    elif command == 'auto-inject':
        task_name = sys.argv[2] if len(sys.argv) > 2 else None
        success, content = plugin.auto_inject_for_active_task(task_name)
        if success:
            print("✅ Auto-injected prompt:")
            print("-" * 40)
            print(content)
        else:
            print(f"❌ Failed: {content}")
    
    elif command == 'monitor':
        plugin.monitor_active_tasks()
    
    elif command == 'watch':
        plugin.watch_task_changes()
    
    elif command == 'create-mapping':
        plugin.create_task_prompt_mapping()
    
    else:
        print("Invalid command or missing arguments")

if __name__ == "__main__":
    main()