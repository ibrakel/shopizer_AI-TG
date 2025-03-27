"""
Java parser utility for extracting method information from Java files.
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple


class JavaMethodParser:
    def __init__(self):
        """Initialize the Java method parser."""
        # Regular expressions for parsing Java code
        self.package_pattern = re.compile(r'package\s+([\w.]+);')
        self.class_pattern = re.compile(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)')
        self.method_pattern = re.compile(
            r'(?:public|private|protected)?\s*'  # Access modifier
            r'(?:static\s+)?'  # Static modifier
            r'(?:final\s+)?'  # Final modifier
            r'(?:abstract\s+)?'  # Abstract modifier
            r'(?:synchronized\s+)?'  # Synchronized modifier
            r'(?:<[^>]+>\s+)?'  # Generic type parameters
            r'([\w.<>[\]]+)\s+'  # Return type
            r'(\w+)\s*'  # Method name
            r'\((.*?)\)\s*'  # Parameters
            r'(?:throws\s+[\w,\s.]+)?'  # Throws clause
            r'(?:\{|;)'  # Method body start or interface method end
        )
        self.parameter_pattern = re.compile(r'([\w.<>[\]]+)\s+(\w+)(?:\s*,\s*)?')

    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Parse a Java file and extract method information.
        
        Args:
            file_path (str): Path to the Java file
            
        Returns:
            List[Dict]: List of method information dictionaries
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract package name
        package_match = self.package_pattern.search(content)
        package_name = package_match.group(1) if package_match else ""

        # Extract class name
        class_match = self.class_pattern.search(content)
        if not class_match:
            return []
        class_name = class_match.group(1)

        # Extract methods
        methods = []
        for match in self.method_pattern.finditer(content):
            return_type = match.group(1)
            method_name = match.group(2)
            parameters_str = match.group(3)

            # Parse parameters and convert to string format expected by the test generator
            parameters = []
            if parameters_str.strip():
                for param_match in self.parameter_pattern.finditer(parameters_str):
                    param_type = param_match.group(1)
                    param_name = param_match.group(2)
                    # Store as a string in the format "type name"
                    parameters.append(f"{param_type} {param_name}")

            # Create method info dictionary
            method_info = {
                "package": package_name,
                "class_name": class_name,
                "name": method_name,
                "return_type": return_type,
                "parameters": parameters,
                "is_public": self._is_public_method(match.group(0)),
                "is_static": self._is_static_method(match.group(0)),
                "is_abstract": self._is_abstract_method(match.group(0))
            }
            methods.append(method_info)

        return methods

    def _is_public_method(self, method_signature: str) -> bool:
        """Check if a method is public."""
        return 'public' in method_signature

    def _is_static_method(self, method_signature: str) -> bool:
        """Check if a method is static."""
        return 'static' in method_signature

    def _is_abstract_method(self, method_signature: str) -> bool:
        """Check if a method is abstract."""
        return 'abstract' in method_signature

    def get_method_dependencies(self, method_info: Dict) -> Set[str]:
        """
        Get dependencies for a method based on its signature.
        
        Args:
            method_info (Dict): Method information dictionary
            
        Returns:
            Set[str]: Set of dependency class names
        """
        dependencies = set()

        # Add return type if it's a class
        return_type = method_info["return_type"]
        if self._is_class_type(return_type):
            dependencies.add(return_type)

        # Add parameter types if they're classes
        for param in method_info["parameters"]:
            # Extract type from "type name" format
            param_type = param.split()[0] if param and ' ' in param else param
            if self._is_class_type(param_type):
                dependencies.add(param_type)

        return dependencies

    def _is_class_type(self, type_name: str) -> bool:
        """
        Check if a type name represents a class (vs primitive type).
        
        Args:
            type_name (str): Type name to check
            
        Returns:
            bool: True if type_name represents a class
        """
        primitives = {
            "void", "boolean", "byte", "char", "short", "int", "long", "float", "double",
            "Boolean", "Byte", "Character", "Short", "Integer", "Long", "Float", "Double",
            "String"
        }
        return (
            type_name not in primitives and
            not type_name.endswith("[]") and  # Array types
            not type_name.startswith("<") and  # Generic type parameters
            "." in type_name  # Qualified class names
        )

    def get_method_body(self, file_path: str, method_name: str) -> Optional[str]:
        """
        Extract the body of a specific method from a Java file.
        
        Args:
            file_path (str): Path to the Java file
            method_name (str): Name of the method to extract
            
        Returns:
            Optional[str]: Method body if found, None otherwise
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the method
        method_start = None
        brace_count = 0
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for method signature
            if method_name in line and re.search(rf'\b{method_name}\b', line):
                if '{' in line:  # Method body starts on the same line
                    method_start = i
                    brace_count = line.count('{') - line.count('}')
                    if brace_count == 0:  # Single-line method
                        return line
                    break
                elif line.strip().endswith('{'):  # Method body starts on the next line
                    method_start = i
                    brace_count = 1
                    break

        if method_start is None:
            return None

        # Extract method body
        body_lines = []
        i = method_start
        while i < len(lines) and brace_count > 0:
            line = lines[i]
            body_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            i += 1

        return '\n'.join(body_lines)

    def get_method_calls(self, method_body: str) -> List[str]:
        """
        Extract method calls from a method body.
        
        Args:
            method_body (str): Method body to analyze
            
        Returns:
            List[str]: List of method names called
        """
        # Simple regex to find method calls
        # This is a basic implementation and might need to be enhanced
        method_call_pattern = re.compile(r'(\w+)\s*\([^)]*\)')
        return [m.group(1) for m in method_call_pattern.finditer(method_body)]

    def get_method_annotations(self, file_path: str, method_name: str) -> List[str]:
        """
        Get annotations for a specific method.
        
        Args:
            file_path (str): Path to the Java file
            method_name (str): Name of the method
            
        Returns:
            List[str]: List of annotation names
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        annotations = []
        
        # Find the method and look for annotations
        for i, line in enumerate(lines):
            if method_name in line and re.search(rf'\b{method_name}\b', line):
                # Look backwards for annotations
                j = i - 1
                while j >= 0 and '@' in lines[j]:
                    annotation = re.search(r'@(\w+)', lines[j])
                    if annotation:
                        annotations.append(annotation.group(1))
                    j -= 1
                break

        return annotations

    def get_method_exceptions(self, method_signature: str) -> List[str]:
        """
        Extract exception types from a method signature.
        
        Args:
            method_signature (str): Method signature to analyze
            
        Returns:
            List[str]: List of exception class names
        """
        # Extract exceptions from throws clause
        throws_pattern = re.compile(r'throws\s+([\w,\s.]+)')
        match = throws_pattern.search(method_signature)
        
        if match:
            # Split and clean exception names
            exceptions = [
                e.strip()
                for e in match.group(1).split(',')
            ]
            return exceptions
        
        return []

    def get_method_modifiers(self, method_signature: str) -> Set[str]:
        """
        Extract modifiers from a method signature.
        
        Args:
            method_signature (str): Method signature to analyze
            
        Returns:
            Set[str]: Set of modifier names
        """
        modifiers = set()
        modifier_pattern = re.compile(
            r'\b(public|private|protected|static|final|abstract|synchronized|native)\b'
        )
        
        for match in modifier_pattern.finditer(method_signature):
            modifiers.add(match.group(1))
            
        return modifiers 