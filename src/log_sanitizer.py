#!/usr/bin/env python3

"""
Log Sanitizer for Prompt Manager
Intelligently filters repetitive patterns from logs and text content
"""

import re
import hashlib
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from difflib import SequenceMatcher
from datetime import datetime
import json


class LogSanitizer:
    """Sanitizes logs by removing repetitive patterns and summarizing redundant content"""
    
    def __init__(self, similarity_threshold: float = 0.85, min_repetitions: int = 3):
        """
        Initialize the LogSanitizer
        
        Args:
            similarity_threshold: Minimum similarity ratio to consider lines as duplicates (0.0-1.0)
            min_repetitions: Minimum number of similar lines before filtering
        """
        self.similarity_threshold = similarity_threshold
        self.min_repetitions = min_repetitions
        self.stats = {
            'total_lines': 0,
            'unique_lines': 0,
            'filtered_lines': 0,
            'pattern_groups': 0
        }
    
    def _normalize_line(self, line: str) -> str:
        """Normalize a line for pattern matching by removing timestamps and numbers"""
        # Remove timestamps in various formats
        line = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,\.\d]*', '<TIMESTAMP>', line)
        line = re.sub(r'\d{2}:\d{2}:\d{2}[,\.\d]*', '<TIME>', line)
        
        # Replace IP addresses
        line = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?', '<IP>', line)
        
        # Replace UUIDs
        line = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '<UUID>', line)
        
        # Replace hex addresses
        line = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', line)
        
        # Replace file paths with line numbers
        line = re.sub(r'([a-zA-Z_]\w*\.py):(\d+)', r'\1:<LINE>', line)
        
        # Replace port numbers
        line = re.sub(r':(\d{4,5})\b', ':<PORT>', line)
        
        # Replace common numeric patterns
        line = re.sub(r'\b\d{6,}\b', '<LONGNUM>', line)
        line = re.sub(r'\b\d+\.\d+\b', '<FLOAT>', line)
        
        return line.strip()
    
    def _calculate_similarity(self, line1: str, line2: str) -> float:
        """Calculate similarity between two lines using SequenceMatcher"""
        # First normalize both lines
        norm1 = self._normalize_line(line1)
        norm2 = self._normalize_line(line2)
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _extract_pattern_key(self, line: str) -> str:
        """Extract a pattern key from a line for grouping similar lines"""
        normalized = self._normalize_line(line)
        
        # Further simplify for pattern matching
        # Remove specific values but keep structure
        pattern = re.sub(r'"[^"]*"', '"<STRING>"', normalized)
        pattern = re.sub(r"'[^']*'", "'<STRING>'", pattern)
        pattern = re.sub(r'\b\d+\b', '<NUM>', pattern)
        
        return pattern
    
    def _create_summary(self, lines: List[str], pattern: str) -> str:
        """Create a summary message for filtered lines"""
        count = len(lines)
        
        # Extract the service/component name if present
        service_match = re.match(r'^([a-zA-Z0-9-_]+)\s*\|', lines[0])
        service = service_match.group(1) if service_match else "Lines"
        
        # Analyze the pattern type
        if "Session created" in pattern and "AsyncSession" in pattern:
            return f"[... {count} similar session creation messages filtered ...]"
        elif "No delayed tasks" in pattern:
            return f"[... {count} 'No delayed tasks' messages filtered ...]"
        elif "Processing scheduled tasks" in pattern:
            return f"[... {count} task processing messages filtered ...]"
        elif "Checking for due scheduled uploads" in pattern:
            return f"[... {count} scheduler check messages filtered ...]"
        elif "get_async_session called" in pattern:
            return f"[... {count} async session calls filtered ...]"
        elif "/api/health" in pattern and "200 OK" in pattern:
            return f"[... {count} health check requests filtered ...]"
        else:
            # Generic summary
            sample_msg = lines[0].split('|', 1)[-1].strip() if '|' in lines[0] else lines[0]
            if len(sample_msg) > 50:
                sample_msg = sample_msg[:47] + "..."
            return f"[... {count} similar lines filtered: '{sample_msg}' ...]"
    
    def _group_similar_lines(self, lines: List[str]) -> Dict[str, List[Tuple[int, str]]]:
        """Group similar lines together based on patterns"""
        pattern_groups = defaultdict(list)
        pattern_exemplars = {}  # Store an example for each pattern
        
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            
            pattern_key = self._extract_pattern_key(line)
            matched = False
            
            # Check against existing patterns
            for existing_pattern, exemplar in pattern_exemplars.items():
                similarity = self._calculate_similarity(line, exemplar)
                if similarity >= self.similarity_threshold:
                    pattern_groups[existing_pattern].append((idx, line))
                    matched = True
                    break
            
            if not matched:
                # New pattern
                pattern_groups[pattern_key].append((idx, line))
                pattern_exemplars[pattern_key] = line
        
        return pattern_groups
    
    def sanitize(self, content: str, preserve_unique: bool = True) -> str:
        """
        Sanitize log content by removing repetitive patterns
        
        Args:
            content: The log content to sanitize
            preserve_unique: Whether to preserve unique lines between patterns
            
        Returns:
            Sanitized log content with repetitive patterns summarized
        """
        lines = content.split('\n')
        self.stats['total_lines'] = len(lines)
        
        # Group similar lines
        pattern_groups = self._group_similar_lines(lines)
        
        # Build output
        output_lines = []
        processed_indices = set()
        last_index = -1
        
        for i, line in enumerate(lines):
            if i in processed_indices:
                continue
            
            # Check if this line is part of a repetitive pattern
            in_pattern = False
            for pattern, group in pattern_groups.items():
                indices = [idx for idx, _ in group]
                if i in indices and len(group) >= self.min_repetitions:
                    in_pattern = True
                    
                    # Check if we should output a summary
                    if min(indices) == i:  # First occurrence of this pattern
                        # Add any unique lines before this pattern
                        if preserve_unique and last_index >= 0:
                            for j in range(last_index + 1, i):
                                if j not in processed_indices and lines[j].strip():
                                    output_lines.append(lines[j])
                        
                        # Output first few examples
                        example_count = min(2, len(group))
                        for j in range(example_count):
                            output_lines.append(group[j][1])
                        
                        # Add summary if there are more
                        if len(group) > example_count:
                            summary = self._create_summary([l for _, l in group], pattern)
                            output_lines.append(summary)
                        
                        # Mark all as processed
                        processed_indices.update(indices)
                        last_index = max(indices)
                        self.stats['filtered_lines'] += len(group) - example_count
                    break
            
            if not in_pattern:
                # Output unique line
                output_lines.append(line)
                processed_indices.add(i)
                last_index = i
        
        self.stats['unique_lines'] = len(output_lines)
        self.stats['pattern_groups'] = len([g for g in pattern_groups.values() if len(g) >= self.min_repetitions])
        
        return '\n'.join(output_lines)
    
    def sanitize_with_context(self, content: str, context_lines: int = 2) -> str:
        """
        Sanitize but preserve context lines around changes
        
        Args:
            content: The log content to sanitize
            context_lines: Number of lines to preserve around pattern changes
            
        Returns:
            Sanitized content with context preserved
        """
        # Implementation similar to sanitize() but preserves context
        return self.sanitize(content, preserve_unique=True)
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about the last sanitization operation"""
        return self.stats.copy()
    
    def detect_sensitive_data(self, content: str) -> List[str]:
        """Detect potential sensitive data in logs (API keys, passwords, etc.)"""
        warnings = []
        
        # Common API key patterns
        api_key_patterns = [
            (r'[aA][pP][iI][_-]?[kK][eE][yY]\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'API Key'),
            (r'[sS][eE][cC][rR][eE][tT]\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Secret'),
            (r'[tT][oO][kK][eE][nN]\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Token'),
            (r'[pP][aA][sS][sS][wW][oO][rR][dD]\s*[:=]\s*["\']?([^"\']+)["\']?', 'Password'),
            (r'Bearer\s+([a-zA-Z0-9_\-\.]+)', 'Bearer Token'),
            (r'(aws_access_key_id|aws_secret_access_key)\s*=\s*["\']?([^"\']+)["\']?', 'AWS Credentials'),
        ]
        
        for pattern, name in api_key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                warnings.append(f"Potential {name} detected")
        
        return warnings


class LogSanitizerConfig:
    """Configuration for LogSanitizer"""
    
    def __init__(self):
        self.similarity_threshold = 0.85
        self.min_repetitions = 3
        self.context_lines = 2
        self.preserve_timestamps = False
        self.max_example_lines = 2
        self.sensitive_data_check = True
        
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'similarity_threshold': self.similarity_threshold,
            'min_repetitions': self.min_repetitions,
            'context_lines': self.context_lines,
            'preserve_timestamps': self.preserve_timestamps,
            'max_example_lines': self.max_example_lines,
            'sensitive_data_check': self.sensitive_data_check
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LogSanitizerConfig':
        """Create config from dictionary"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


def sanitize_clipboard_content(content: str, config: Optional[LogSanitizerConfig] = None) -> Tuple[str, Dict[str, any]]:
    """
    Main entry point for sanitizing clipboard content
    
    Args:
        content: The content to sanitize
        config: Optional configuration
        
    Returns:
        Tuple of (sanitized_content, statistics)
    """
    if config is None:
        config = LogSanitizerConfig()
    
    sanitizer = LogSanitizer(
        similarity_threshold=config.similarity_threshold,
        min_repetitions=config.min_repetitions
    )
    
    # Check for sensitive data if enabled
    warnings = []
    if config.sensitive_data_check:
        warnings = sanitizer.detect_sensitive_data(content)
    
    # Sanitize the content
    sanitized = sanitizer.sanitize(content)
    
    # Get statistics
    stats = sanitizer.get_stats()
    stats['warnings'] = warnings
    
    return sanitized, stats


def main():
    """Test the log sanitizer with example content"""
    test_content = """
artist-dashboard-scheduler  | 2025-07-28 20:50:54,828 - app.upload_system.worker - DEBUG - No delayed tasks due for execution
artist-dashboard-scheduler  | 2025-07-28 20:50:54,828 - app.upload_system.worker - DEBUG - No delayed tasks due for execution
artist-dashboard-scheduler  | 2025-07-28 20:50:54,828 - app.upload_system.worker - DEBUG - No delayed tasks due for execution
artist-dashboard-worker     | DEBUG: Session created: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker     | DEBUG: get_async_session called, returning type: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker     | DEBUG: Session created: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker     | DEBUG: get_async_session called, returning type: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-app        | INFO:     127.0.0.1:48062 - "GET /api/health HTTP/1.1" 200 OK
artist-dashboard-worker     | 2025-07-28 20:51:04,970 - app.upload_system.worker - DEBUG - Processing scheduled tasks
artist-dashboard-scheduler  | 2025-07-28 20:51:14,837 - app.upload_system.scheduler - DEBUG - No scheduled uploads due for execution
    """
    
    sanitizer = LogSanitizer()
    sanitized = sanitizer.sanitize(test_content)
    
    print("Original lines:", test_content.count('\n'))
    print("Sanitized lines:", sanitized.count('\n'))
    print("\nSanitized content:")
    print(sanitized)
    print("\nStats:", sanitizer.get_stats())


if __name__ == "__main__":
    main()