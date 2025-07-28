#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
from typing import Dict, List, Optional
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt_manager import PromptManager
from project_registry import ProjectRegistry

app = Flask(__name__)
CORS(app)

pm = PromptManager()
registry = ProjectRegistry()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for connection testing"""
    return jsonify({
        'status': 'healthy',
        'service': 'Prompt Manager API',
        'version': '1.0.0'
    })

@app.route('/api/prompts', methods=['GET'])
def list_prompts():
    category = request.args.get('category')
    tag = request.args.get('tag')
    search = request.args.get('search')
    context = request.args.get('context')
    
    prompts = pm.prompts["prompts"]
    
    if category:
        prompts = [p for p in prompts if p["category"] == category]
    
    if tag:
        prompts = [p for p in prompts if tag in p["tags"]]
    
    if search:
        search_lower = search.lower()
        prompts = [p for p in prompts 
                   if search_lower in p["title"].lower() or 
                      search_lower in p["content"].lower()]
    
    if context:
        prompts = analyze_context_and_filter(prompts, context)
    
    prompts = sorted(prompts, key=lambda x: x['used_count'], reverse=True)
    
    return jsonify(prompts)

@app.route('/api/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    prompt = pm.get_prompt(prompt_id)
    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404
    return jsonify(prompt)

@app.route('/api/prompts/<int:prompt_id>/render', methods=['POST'])
def render_prompt(prompt_id):
    prompt = pm.get_prompt(prompt_id)
    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404
    
    variables = request.json.get('variables', {})
    content = prompt["content"]
    
    missing_vars = []
    for var in prompt.get("variables", []):
        if var in variables:
            content = content.replace(f"{{{var}}}", variables[var])
        elif var in pm.prompts.get("variables", {}) and pm.prompts["variables"][var].get("default_value"):
            content = content.replace(f"{{{var}}}", pm.prompts["variables"][var]["default_value"])
        else:
            missing_vars.append(var)
    
    if missing_vars:
        return jsonify({
            "error": "Missing variables",
            "missing": missing_vars
        }), 400
    
    prompt["used_count"] += 1
    pm._save_prompts()
    
    return jsonify({
        "content": content,
        "prompt_id": prompt_id,
        "title": prompt["title"]
    })

@app.route('/api/prompts/suggest', methods=['POST'])
def suggest_prompts():
    context = request.json.get('context', {})
    
    current_task = context.get('current_task', '')
    file_type = context.get('file_type', '')
    error_present = context.get('has_error', False)
    is_planning = context.get('is_planning', False)
    
    suggestions = []
    
    if error_present:
        suggestions.extend(filter_by_category('debugging'))
    
    if is_planning:
        suggestions.extend(filter_by_category('planning'))
        suggestions.extend(filter_by_category('project-management'))
    
    if file_type:
        if file_type in ['py', 'js', 'ts', 'java', 'go']:
            suggestions.extend(filter_by_category('development'))
        elif file_type in ['md', 'txt', 'rst']:
            suggestions.extend(filter_by_category('documentation'))
    
    if 'test' in current_task.lower():
        suggestions.extend(filter_by_tags(['testing', 'test']))
    
    if 'api' in current_task.lower():
        suggestions.extend(filter_by_tags(['api']))
    
    seen = set()
    unique_suggestions = []
    for prompt in suggestions:
        if prompt['id'] not in seen:
            seen.add(prompt['id'])
            unique_suggestions.append(prompt)
    
    unique_suggestions = sorted(unique_suggestions, 
                              key=lambda x: (x['used_count'], -x['id']), 
                              reverse=True)[:5]
    
    return jsonify(unique_suggestions)

@app.route('/api/prompts/<int:prompt_id>/track', methods=['POST'])
def track_usage(prompt_id):
    success = request.json.get('success', True)
    duration = request.json.get('duration')
    
    prompt = pm.get_prompt(prompt_id)
    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404
    
    if 'analytics' not in prompt:
        prompt['analytics'] = {
            'success_count': 0,
            'failure_count': 0,
            'total_duration': 0,
            'avg_duration': 0
        }
    
    if success:
        prompt['analytics']['success_count'] += 1
    else:
        prompt['analytics']['failure_count'] += 1
    
    if duration:
        prompt['analytics']['total_duration'] += duration
        total_uses = prompt['analytics']['success_count'] + prompt['analytics']['failure_count']
        prompt['analytics']['avg_duration'] = prompt['analytics']['total_duration'] / total_uses
    
    pm._save_prompts()
    
    return jsonify({"status": "tracked"})

def analyze_context_and_filter(prompts: List[Dict], context: str) -> List[Dict]:
    context_lower = context.lower()
    
    keyword_category_map = {
        'bug': 'debugging',
        'error': 'debugging',
        'fix': 'debugging',
        'review': 'development',
        'implement': 'development',
        'feature': 'planning',
        'design': 'planning',
        'test': 'testing',
        'api': 'testing',
        'document': 'documentation'
    }
    
    relevant_categories = set()
    for keyword, category in keyword_category_map.items():
        if keyword in context_lower:
            relevant_categories.add(category)
    
    if relevant_categories:
        return [p for p in prompts if p['category'] in relevant_categories]
    
    return prompts

def filter_by_category(category: str) -> List[Dict]:
    return [p for p in pm.prompts["prompts"] if p["category"] == category]

def filter_by_tags(tags: List[str]) -> List[Dict]:
    return [p for p in pm.prompts["prompts"] if any(tag in p["tags"] for tag in tags)]

# Project endpoints
@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all registered Task-Master projects"""
    try:
        projects = registry.list_projects()
        return jsonify(projects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/discover', methods=['POST'])
def discover_projects():
    """Discover new Task-Master projects"""
    try:
        search_paths = request.json.get('paths') if request.json else None
        discovered = registry.discover_projects(search_paths)
        
        # Optionally register them
        register = request.json.get('register', False) if request.json else False
        if register:
            registry.register_projects(discovered)
        
        return jsonify({
            "discovered": discovered,
            "registered": register
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details by ID"""
    project = registry.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project)

@app.route('/api/projects/<project_id>/context', methods=['GET'])
def get_project_context(project_id):
    """Get project context and variables for prompts"""
    try:
        result = registry.get_project_context(project_id)
        if not result:
            return jsonify({"error": "Project not found or unable to extract context"}), 404
        
        context, variables = result
        project = registry.get_project(project_id)
        
        return jsonify({
            "project_id": project_id,
            "project_name": project['name'],
            "context": context,
            "variables": variables
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/current', methods=['GET'])
def get_current_project():
    """Get the current active project"""
    current = registry.get_current_project()
    if not current:
        return jsonify({"error": "No current project set"}), 404
    return jsonify(current)

@app.route('/api/projects/current', methods=['POST'])
def set_current_project():
    """Set the current active project"""
    project_id = request.json.get('project_id')
    if not project_id:
        return jsonify({"error": "project_id required"}), 400
    
    if registry.set_current_project(project_id):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Project not found"}), 404

@app.route('/api/projects/auto-detect', methods=['POST'])
def auto_detect_project():
    """Auto-detect current project based on working directory"""
    cwd = request.json.get('cwd') if request.json else None
    project = registry.auto_detect_current_project(cwd)
    
    if project:
        return jsonify(project)
    else:
        return jsonify({"error": "No Task-Master project detected"}), 404

@app.route('/api/projects/add', methods=['POST'])
def add_project():
    """Manually add a project"""
    try:
        data = request.json
        name = data.get('name')
        path = data.get('path') 
        task_master_dir = data.get('task_master_dir')
        
        if not name or not path:
            return jsonify({"error": "name and path are required"}), 400
        
        project_id = registry.add_project_manually(name, path, task_master_dir)
        project = registry.get_project(project_id)
        
        return jsonify(project), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Remove a project"""
    if registry.remove_project(project_id):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Project not found"}), 404

@app.route('/api/projects/<project_id>/toggle', methods=['POST'])
def toggle_project(project_id):
    """Enable/disable a project"""
    enabled = request.json.get('enabled', True)
    
    if enabled:
        success = registry.enable_project(project_id)
    else:
        success = registry.disable_project(project_id)
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Project not found"}), 404

@app.route('/api/projects/<project_id>/refresh', methods=['POST'])
def refresh_project(project_id):
    """Refresh project information"""
    if registry.refresh_project(project_id):
        project = registry.get_project(project_id)
        return jsonify(project)
    else:
        return jsonify({"error": "Project not found or refresh failed"}), 404

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get registry settings"""
    return jsonify(registry.get_project_settings())

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update registry settings"""
    try:
        settings = request.json
        registry.update_settings(**settings)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)