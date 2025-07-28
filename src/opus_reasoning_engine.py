#!/usr/bin/env python3

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from collections import defaultdict

class OpusReasoningEngine:
    def __init__(self, api_key: str = None, openrouter_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.openrouter_key = openrouter_key or os.getenv('OPENROUTER_API_KEY')
        self.model = "claude-3-opus-20240229"
        self.usage_history = []
        self.prompt_effectiveness = defaultdict(lambda: {'success': 0, 'total': 0})
    
    def analyze_prompt_effectiveness(self, prompt_id: int, task_context: Dict, outcome: Dict) -> Dict:
        """Use Opus to analyze why a prompt was effective or not"""
        
        analysis_prompt = f"""Analyze the effectiveness of this prompt usage:

Prompt ID: {prompt_id}
Task Context: {json.dumps(task_context, indent=2)}
Outcome: {json.dumps(outcome, indent=2)}

Please analyze:
1. Why this prompt was/wasn't effective for this task
2. What context factors influenced the outcome
3. Suggestions for prompt improvement
4. Alternative prompts that might work better

Provide structured analysis with actionable insights."""

        try:
            if self.openrouter_key:
                response = self._call_openrouter(analysis_prompt)
            else:
                response = self._call_anthropic(analysis_prompt)
            
            return {
                'analysis': response,
                'timestamp': datetime.now().isoformat(),
                'prompt_id': prompt_id,
                'context': task_context
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_context_aware_prompt(self, task_description: str, existing_prompts: List[Dict]) -> Dict:
        """Use Opus to generate a new prompt based on task requirements"""
        
        generation_prompt = f"""Based on this task description, generate an optimal prompt template:

Task: {task_description}

Existing similar prompts:
{json.dumps(existing_prompts[:3], indent=2)}

Generate a new prompt that:
1. Addresses the specific task requirements
2. Includes appropriate variable placeholders
3. Follows best practices for AI instruction
4. Is reusable for similar tasks

Return in this JSON format:
{{
    "title": "Descriptive title",
    "content": "The prompt template with {{variables}}",
    "category": "appropriate category",
    "tags": ["relevant", "tags"],
    "variables": ["list", "of", "variables"],
    "reasoning": "Why this prompt structure was chosen"
}}"""

        try:
            if self.openrouter_key:
                response = self._call_openrouter(generation_prompt)
            else:
                response = self._call_anthropic(generation_prompt)
            
            return json.loads(response)
        except Exception as e:
            return {'error': str(e)}
    
    def optimize_prompt_selection(self, task_context: Dict, available_prompts: List[Dict]) -> List[Dict]:
        """Use Opus to rank and optimize prompt selection"""
        
        optimization_prompt = f"""Given this task context and available prompts, rank them by suitability:

Task Context:
{json.dumps(task_context, indent=2)}

Available Prompts:
{json.dumps(available_prompts, indent=2)}

For each prompt:
1. Score its relevance (0-100)
2. Explain why it would/wouldn't work
3. Suggest variable values if applicable
4. Recommend modifications if needed

Return ranked list with scores and reasoning."""

        try:
            if self.openrouter_key:
                response = self._call_openrouter(optimization_prompt)
            else:
                response = self._call_anthropic(optimization_prompt)
            
            # Parse and structure the response
            return self._parse_ranking_response(response, available_prompts)
        except Exception as e:
            return available_prompts  # Fallback to original order
    
    def learn_from_usage_patterns(self, usage_data: List[Dict]) -> Dict:
        """Analyze usage patterns to improve future recommendations"""
        
        learning_prompt = f"""Analyze these prompt usage patterns to identify trends and improvements:

Usage Data:
{json.dumps(usage_data[-50:], indent=2)}  # Last 50 uses

Identify:
1. Common success/failure patterns
2. Context factors that predict success
3. Prompt combinations that work well together
4. Gaps in the current prompt library
5. Recommendations for new prompts or categories

Provide actionable insights for improving the prompt management system."""

        try:
            if self.openrouter_key:
                response = self._call_openrouter(learning_prompt)
            else:
                response = self._call_anthropic(learning_prompt)
            
            insights = {
                'analysis': response,
                'timestamp': datetime.now().isoformat(),
                'data_points': len(usage_data),
                'recommendations': self._extract_recommendations(response)
            }
            
            return insights
        except Exception as e:
            return {'error': str(e)}
    
    def suggest_prompt_improvements(self, prompt: Dict, usage_stats: Dict) -> Dict:
        """Suggest improvements for a specific prompt based on usage"""
        
        improvement_prompt = f"""Analyze this prompt and suggest improvements:

Prompt:
{json.dumps(prompt, indent=2)}

Usage Statistics:
{json.dumps(usage_stats, indent=2)}

Consider:
1. Common variable values used
2. Success/failure rates in different contexts
3. User modifications or complaints
4. Current AI best practices

Suggest:
1. Improved wording or structure
2. Additional variables that might be useful
3. Better default values
4. Category or tag changes
5. When this prompt should/shouldn't be used

Provide specific, actionable improvements."""

        try:
            if self.openrouter_key:
                response = self._call_openrouter(improvement_prompt)
            else:
                response = self._call_anthropic(improvement_prompt)
            
            return {
                'original_prompt': prompt,
                'suggestions': response,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API with Opus model"""
        headers = {
            'Authorization': f'Bearer {self.openrouter_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/promptmanager',
            'X-Title': 'Prompt Manager Reasoning Engine'
        }
        
        data = {
            'model': 'anthropic/claude-3-opus',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API directly"""
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
    
    def _parse_ranking_response(self, response: str, prompts: List[Dict]) -> List[Dict]:
        """Parse Opus ranking response and reorder prompts"""
        # Simple implementation - in production, use more sophisticated parsing
        try:
            lines = response.split('\n')
            scores = {}
            
            for line in lines:
                for prompt in prompts:
                    if str(prompt['id']) in line and 'score' in line.lower():
                        # Extract score (simple regex approach)
                        import re
                        score_match = re.search(r'(\d+)(?:/100)?', line)
                        if score_match:
                            scores[prompt['id']] = int(score_match.group(1))
            
            # Sort prompts by score
            return sorted(prompts, key=lambda p: scores.get(p['id'], 0), reverse=True)
        except:
            return prompts
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract actionable recommendations from analysis"""
        recommendations = []
        lines = analysis.split('\n')
        
        in_recommendations = False
        for line in lines:
            if 'recommendation' in line.lower() or 'suggest' in line.lower():
                in_recommendations = True
            elif in_recommendations and line.strip().startswith('-'):
                recommendations.append(line.strip()[1:].strip())
        
        return recommendations

class PromptSuccessPredictor:
    """ML-based success prediction for prompts"""
    
    def __init__(self):
        self.feature_weights = {
            'category_match': 0.3,
            'tag_overlap': 0.2,
            'usage_frequency': 0.15,
            'success_rate': 0.25,
            'recency': 0.1
        }
    
    def predict_success(self, prompt: Dict, context: Dict, historical_data: List[Dict]) -> float:
        """Predict success probability of a prompt in given context"""
        
        features = self._extract_features(prompt, context, historical_data)
        score = sum(features[k] * self.feature_weights[k] for k in self.feature_weights)
        
        return min(max(score, 0.0), 1.0)
    
    def _extract_features(self, prompt: Dict, context: Dict, historical_data: List[Dict]) -> Dict:
        """Extract features for prediction"""
        features = {}
        
        # Category match
        features['category_match'] = 1.0 if prompt['category'] == context.get('task_type') else 0.0
        
        # Tag overlap
        context_tags = set(context.get('technologies', []))
        prompt_tags = set(prompt.get('tags', []))
        features['tag_overlap'] = len(context_tags & prompt_tags) / max(len(context_tags), 1)
        
        # Usage frequency (normalized)
        max_usage = max((p['used_count'] for p in historical_data), default=1)
        features['usage_frequency'] = prompt['used_count'] / max_usage
        
        # Success rate
        analytics = prompt.get('analytics', {})
        total_uses = analytics.get('success_count', 0) + analytics.get('failure_count', 0)
        features['success_rate'] = analytics.get('success_count', 0) / max(total_uses, 1)
        
        # Recency (how recently was it used successfully)
        features['recency'] = self._calculate_recency_score(prompt, historical_data)
        
        return features
    
    def _calculate_recency_score(self, prompt: Dict, historical_data: List[Dict]) -> float:
        """Calculate recency score based on last successful use"""
        # Simplified implementation
        return 0.5  # Placeholder

if __name__ == "__main__":
    # Example usage
    engine = OpusReasoningEngine()
    
    task_context = {
        'task_type': 'debugging',
        'technologies': ['python', 'api'],
        'is_bug_fix': True
    }
    
    # Test prompt optimization
    available_prompts = [
        {'id': 1, 'title': 'Code Review', 'category': 'development'},
        {'id': 2, 'title': 'Bug Analysis', 'category': 'debugging'},
        {'id': 3, 'title': 'Feature Design', 'category': 'planning'}
    ]
    
    optimized = engine.optimize_prompt_selection(task_context, available_prompts)
    print("Optimized prompt order:", [p['title'] for p in optimized])