"""
Coverage tracking module for test generation.
"""

import os
import re
from typing import Dict, List, Optional
import coverage


class CoverageTracker:
    """
    Tracks test coverage for generated tests.
    """
    
    def __init__(self):
        """Initialize coverage tracker."""
        self.cov = coverage.Coverage()
        self.method_coverage: Dict[str, float] = {}
        
    def start(self):
        """Start coverage tracking."""
        self.cov.start()
        
    def stop(self):
        """Stop coverage tracking."""
        self.cov.stop()
        
    def save(self):
        """Save coverage data."""
        self.cov.save()
        
    def get_coverage(self, method_name: str) -> float:
        """Get coverage percentage for a method."""
        return self.method_coverage.get(method_name, 0.0)
        
    def update_coverage(self, method_name: str, coverage: float):
        """Update coverage for a method."""
        self.method_coverage[method_name] = coverage
        
    def analyze_coverage(self, source_file: str) -> Dict[str, float]:
        """
        Analyze coverage for all methods in a file.
        
        Args:
            source_file (str): Path to source file
            
        Returns:
            Dict[str, float]: Method coverage percentages
        """
        self.cov.load()
        analysis = self.cov.analysis2(source_file)
        
        # Get executed lines
        executed = set(analysis.executed)
        
        # Parse file to get method ranges
        with open(source_file, 'r') as f:
            content = f.read()
            
        method_ranges = self._get_method_ranges(content)
        
        # Calculate coverage for each method
        coverage = {}
        for method_name, (start, end) in method_ranges.items():
            method_lines = set(range(start, end + 1))
            covered_lines = len(method_lines.intersection(executed))
            total_lines = len(method_lines)
            coverage[method_name] = covered_lines / total_lines if total_lines > 0 else 0.0
            
        return coverage
        
    def _get_method_ranges(self, content: str) -> Dict[str, tuple]:
        """
        Get line ranges for each method in the file.
        
        Args:
            content (str): File content
            
        Returns:
            Dict[str, tuple]: Method names mapped to (start_line, end_line)
        """
        method_ranges = {}
        lines = content.split('\n')
        
        # Simple method detection - can be improved
        method_pattern = r'(?:public|private|protected)?\s+(?:static\s+)?(\w+)\s+(\w+)\s*\('
        
        current_method = None
        start_line = None
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            if current_method is None:
                match = re.search(method_pattern, line)
                if match:
                    current_method = match.group(2)
                    start_line = i
                    brace_count = line.count('{') - line.count('}')
            else:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    method_ranges[current_method] = (start_line, i)
                    current_method = None
                    
        return method_ranges 