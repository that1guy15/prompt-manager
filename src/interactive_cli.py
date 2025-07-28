#!/usr/bin/env python3

import os
import sys
import json
import requests
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import readline
import atexit
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt_manager import PromptManager
from opus_reasoning_engine import OpusReasoningEngine, PromptSuccessPredictor

class InteractivePromptCLI:
    def __init__(self, api_url: str = "http://localhost:5000/api"):
        self.api_url = api_url
        self.pm = PromptManager()
        self.reasoning_engine = OpusReasoningEngine()
        self.predictor = PromptSuccessPredictor()
        self.history_file = os.path.expanduser('~/.prompt_manager_history')
        self.current_context = {}
        self._setup_readline()
    
    def _setup_readline(self):
        """Setup readline for better CLI experience"""
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        
        atexit.register(readline.write_history_file, self.history_file)
    
    def _completer(self, text: str, state: int):
        """Tab completion for commands"""
        commands = ['suggest', 'use', 'search', 'quick', 'context', 'history', 'learn', 'exit']
        matches = [cmd for cmd in commands if cmd.startswith(text)]
        return matches[state] if state < len(matches) else None
    
    def run(self):
        """Main interactive loop"""
        print("🚀 Prompt Manager Interactive CLI")
        print("Commands: suggest, use <id>, search <term>, quick, context, history, learn, exit")
        print("-" * 50)
        
        self._detect_context()
        
        while True:
            try:
                command = input("\nprompt> ").strip()
                if not command:
                    continue
                
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd == 'exit':
                    break
                elif cmd == 'suggest':
                    self._suggest_prompts()
                elif cmd == 'use':
                    self._use_prompt(args)
                elif cmd == 'search':
                    self._search_prompts(args)
                elif cmd == 'quick':
                    self._quick_prompt()
                elif cmd == 'context':
                    self._show_context()
                elif cmd == 'history':
                    self._show_history()
                elif cmd == 'learn':
                    self._learn_from_usage()
                else:
                    print(f"Unknown command: {cmd}")
            
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")
    
    def _detect_context(self):
        """Auto-detect current context"""
        self.current_context = {
            'cwd': os.getcwd(),
            'git_branch': self._get_git_branch(),
            'recent_files': self._get_recent_files(),
            'has_errors': self._check_for_errors(),
            'project_type': self._detect_project_type()
        }
        
        print(f"📍 Context: {self.current_context['cwd']}")
        if self.current_context['git_branch']:
            print(f"🌿 Branch: {self.current_context['git_branch']}")
    
    def _suggest_prompts(self):
        """Suggest prompts based on current context"""
        print("\n🤔 Analyzing context...")
        
        # Build context for API
        api_context = {
            'current_task': self._infer_task_from_branch(),
            'file_type': self._get_primary_file_type(),
            'has_error': self.current_context['has_errors'],
            'is_planning': 'feature' in self.current_context.get('git_branch', '').lower()
        }
        
        try:
            # Get suggestions from API
            response = requests.post(f"{self.api_url}/prompts/suggest", json={'context': api_context})
            if response.status_code == 200:
                suggestions = response.json()
                
                # Use Opus to optimize if available
                if self.reasoning_engine.openrouter_key:
                    suggestions = self.reasoning_engine.optimize_prompt_selection(api_context, suggestions)
                
                # Add success predictions
                for prompt in suggestions:
                    prompt['predicted_success'] = self.predictor.predict_success(
                        prompt, api_context, self.pm.prompts["prompts"]
                    )
                
                # Display suggestions
                print("\n📋 Suggested prompts:")
                for i, prompt in enumerate(suggestions[:5], 1):
                    success_indicator = "⭐" * int(prompt.get('predicted_success', 0.5) * 5)
                    print(f"{i}. [{prompt['id']}] {prompt['title']} - {prompt['category']} {success_indicator}")
                    print(f"   Used: {prompt['used_count']} times | Tags: {', '.join(prompt['tags'][:3])}")
                
                # Quick selection
                choice = input("\nSelect (1-5) or press Enter to skip: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                    self._use_prompt(str(suggestions[int(choice)-1]['id']))
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
    
    def _use_prompt(self, prompt_id_str: str):
        """Use a specific prompt"""
        try:
            prompt_id = int(prompt_id_str)
            prompt = self.pm.get_prompt(prompt_id)
            
            if not prompt:
                print(f"Prompt {prompt_id} not found")
                return
            
            print(f"\n📝 Using: {prompt['title']}")
            
            # Collect variables
            variables = {}
            for var in prompt.get('variables', []):
                default = ""
                if var in self.pm.prompts.get('variables', {}):
                    default = self.pm.prompts['variables'][var].get('default_value', '')
                
                value = input(f"{var} [{default}]: ").strip() or default
                variables[var] = value
            
            # Render prompt
            response = requests.post(f"{self.api_url}/prompts/{prompt_id}/render", 
                                   json={'variables': variables})
            
            if response.status_code == 200:
                result = response.json()
                content = result['content']
                
                # Copy to clipboard
                if sys.platform == "darwin":
                    subprocess.run(["pbcopy"], input=content, text=True, check=True)
                    print("✅ Copied to clipboard!")
                else:
                    print("\n" + "-" * 50)
                    print(content)
                    print("-" * 50)
                
                # Track usage
                self._track_usage_start(prompt_id)
            else:
                print(f"Error: {response.json().get('error', 'Unknown error')}")
        
        except ValueError:
            print(f"Invalid prompt ID: {prompt_id_str}")
    
    def _quick_prompt(self):
        """Quick access to most used prompts"""
        prompts = sorted(self.pm.prompts["prompts"], 
                        key=lambda x: x['used_count'], 
                        reverse=True)[:5]
        
        print("\n⚡ Quick access (most used):")
        for i, prompt in enumerate(prompts, 1):
            print(f"{i}. {prompt['title']} (used {prompt['used_count']} times)")
        
        choice = input("\nSelect (1-5): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(prompts):
            self._use_prompt(str(prompts[int(choice)-1]['id']))
    
    def _search_prompts(self, search_term: str):
        """Search prompts"""
        if not search_term:
            search_term = input("Search for: ").strip()
        
        try:
            response = requests.get(f"{self.api_url}/prompts?search={search_term}")
            if response.status_code == 200:
                prompts = response.json()
                
                if not prompts:
                    print("No prompts found")
                    return
                
                print(f"\n🔍 Found {len(prompts)} prompts:")
                for prompt in prompts[:10]:
                    print(f"[{prompt['id']}] {prompt['title']} - {prompt['category']}")
                    print(f"    Tags: {', '.join(prompt['tags'])}")
        
        except Exception as e:
            print(f"Error searching: {e}")
    
    def _show_context(self):
        """Show current context"""
        print("\n📊 Current Context:")
        print(json.dumps(self.current_context, indent=2))
    
    def _show_history(self):
        """Show usage history"""
        usage_history = []
        for prompt in self.pm.prompts["prompts"]:
            if prompt['used_count'] > 0:
                usage_history.append({
                    'title': prompt['title'],
                    'count': prompt['used_count'],
                    'category': prompt['category'],
                    'last_used': prompt.get('last_used', 'Unknown')
                })
        
        usage_history.sort(key=lambda x: x['count'], reverse=True)
        
        print("\n📈 Usage History:")
        for item in usage_history[:10]:
            print(f"{item['title']} - {item['count']} uses ({item['category']})")
    
    def _learn_from_usage(self):
        """Use Opus to learn from usage patterns"""
        if not self.reasoning_engine.openrouter_key:
            print("Opus integration not configured. Set OPENROUTER_API_KEY.")
            return
        
        print("\n🧠 Analyzing usage patterns with Opus...")
        
        # Prepare usage data
        usage_data = []
        for prompt in self.pm.prompts["prompts"]:
            if prompt['used_count'] > 0:
                usage_data.append({
                    'prompt_id': prompt['id'],
                    'title': prompt['title'],
                    'category': prompt['category'],
                    'used_count': prompt['used_count'],
                    'analytics': prompt.get('analytics', {})
                })
        
        insights = self.reasoning_engine.learn_from_usage_patterns(usage_data)
        
        if 'error' not in insights:
            print("\n💡 Insights:")
            print(insights.get('analysis', 'No insights available'))
            
            recommendations = insights.get('recommendations', [])
            if recommendations:
                print("\n🎯 Recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"{i}. {rec}")
    
    def _track_usage_start(self, prompt_id: int):
        """Track when a prompt is used"""
        self.current_usage = {
            'prompt_id': prompt_id,
            'start_time': datetime.now(),
            'context': self.current_context.copy()
        }
    
    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return None
    
    def _get_recent_files(self) -> List[str]:
        """Get recently modified files"""
        try:
            result = subprocess.run(['find', '.', '-type', 'f', '-mtime', '-1', 
                                   '-not', '-path', '*/\.*'], 
                                  capture_output=True, text=True)
            return result.stdout.strip().split('\n')[:10]
        except:
            return []
    
    def _check_for_errors(self) -> bool:
        """Check if there are error indicators in recent output"""
        # Simplified check - in production, analyze actual error logs
        return any('error' in f.lower() or 'bug' in f.lower() 
                  for f in self._get_recent_files())
    
    def _detect_project_type(self) -> str:
        """Detect project type based on files"""
        if os.path.exists('package.json'):
            return 'javascript'
        elif os.path.exists('requirements.txt') or os.path.exists('setup.py'):
            return 'python'
        elif os.path.exists('go.mod'):
            return 'go'
        else:
            return 'unknown'
    
    def _infer_task_from_branch(self) -> str:
        """Infer current task from git branch name"""
        branch = self.current_context.get('git_branch', '')
        if 'feature' in branch:
            return 'feature development'
        elif 'fix' in branch or 'bug' in branch:
            return 'bug fixing'
        elif 'refactor' in branch:
            return 'refactoring'
        else:
            return 'development'
    
    def _get_primary_file_type(self) -> str:
        """Get primary file type in current directory"""
        extensions = defaultdict(int)
        try:
            for file in Path('.').rglob('*'):
                if file.is_file() and not str(file).startswith('.'):
                    ext = file.suffix[1:] if file.suffix else ''
                    if ext:
                        extensions[ext] += 1
        except:
            pass
        
        if extensions:
            return max(extensions, key=extensions.get)
        return ''

def main():
    cli = InteractivePromptCLI()
    cli.run()

if __name__ == "__main__":
    main()