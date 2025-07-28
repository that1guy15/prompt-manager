"""
Prompt Manager - AI Prompt Management and Task-Master Integration System

A powerful CLI tool and browser extension for managing AI prompts with 
context-aware suggestions, multi-project support, and seamless browser integration.
"""

__version__ = "0.0.16"
__author__ = "Prompt Manager Team"
__email__ = "team@promptmanager.dev"

from .core import PromptManager
from .project_registry import ProjectRegistry
from .context_extractor import TaskMasterContextExtractor

__all__ = [
    "PromptManager", 
    "ProjectRegistry", 
    "TaskMasterContextExtractor"
]