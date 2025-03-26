"""
Java source code parser for extracting method information from the Shopizer repository.
This module uses regular expressions to locate and parse classes, methods, and their signatures.
"""

import os
import re
from typing import List, Dict, Tuple, Optional, Any
from config.settings import Config
import javalang
from dataclasses import dataclass


class JavaMethod:
    """
    Represents a Java method with all its properties needed for test generation.
    """
    def __init__(self, class_name: str, package_name: str, 
                 method_name: str, access_modifier: str, 
                 return_type: str, parameters: List[Tuple[str, str]], 
                 exceptions: List[str], is_static: bool, 
                 source_file: str, line_number: int, 
                 body: str = ""):
        """
        Initialize a JavaMethod object with all its properties.
        
        Args:
            class_name (str): Name of the class containing the method
            package_name (str): Package of the class
            method_name (str): Name of the method
            access_modifier (str): Access modifier (public, private, protected)
            return_type (str): Return type of the method
            parameters (List[Tuple[str, str]]): List of (type, name) tuples for parameters
            exceptions (List[str]): List of exceptions thrown by the method
            is_static (bool): Whether the method is static
            source_file (str): Path to the source file
            line_number (int): Line number where the method starts
            body (str, optional): Method body if available
        """
        self.class_name = class_name
        self.package_name = package_name
        self.method_name = method_name
        self.access_modifier = access_modifier
        self.return_type = return_type
        self.parameters = parameters
        self.exceptions = exceptions
        self.is_static = is_static
        self.source_file = source_file
        self.line_number = line_number
        self.body = body

    def get_qualified_name(self) -> str:
        """
        Returns the fully qualified name of the method.
        
        Returns:
            str: Fully qualified method name (package.class.method)
        """
        return f"{self.package_name}.{self.class_name}.{self.method_name}"

    def get_parameter_types(self) -> List[str]:
        """
        Returns a list of parameter types.
        
        Returns:
            List[str]: List of parameter types
        """
        return [param[0] for param in self.parameters]

    def get_parameter_names(self) -> List[str]:
        """
        Returns a list of parameter names.
        
        Returns:
            List[str]: List of parameter names
        """
        return [param[1] for param in self.parameters]

    def has_parameters(self) -> bool:
        """
        Returns whether the method has parameters.
        
        Returns:
            bool: True if method has parameters, False otherwise
        """
        return len(self.parameters) > 0

    def __str__(self) -> str:
        """
        Returns a string representation of the method.
        
        Returns:
            str: String representation of the method
        """
        params = ", ".join([f"{ptype} {pname}" for ptype, pname in self.parameters])
        static = "static " if self.is_static else ""
        exceptions = f" throws {', '.join(self.exceptions)}" if self.exceptions else ""
        return f"{self.access_modifier} {static}{self.return_type} {self.method_name}({params}){exceptions}"


class JavaParser:
    """
    Parses Java source files to extract classes and methods.
    """
    def __init__(self, base_dir: str = None):
        """
        Initialize the Java parser.
        
        Args:
            base_dir (str, optional): Base directory of the repository
        """
        self.base_dir = base_dir or os.path.join(os.getcwd(), Config.SOURCE_DIRS[0])
        self.methods: List[JavaMethod] = []

    def parse_repository(self) -> List[JavaMethod]:
        """
        Parse the entire repository and collect all methods.
        
        Returns:
            List[JavaMethod]: List of all methods found in the repository
        """
        self.methods = []
        
        # Process each source directory in the config
        for source_dir in Config.SOURCE_DIRS:
            full_path = os.path.join(self.base_dir, source_dir)
            if not os.path.exists(full_path):
                print(f"Warning: Source directory {full_path} not found. Skipping.")
                continue
            
            # Walk through all java files in the directory
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith(".java"):
                        file_path = os.path.join(root, file)
                        self._parse_file(file_path)
        
        return self.methods

    def _parse_file(self, file_path: str) -> None:
        """
        Parse a single Java file and extract methods.
        
        Args:
            file_path (str): Path to the Java file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract package
            package_match = re.search(r'package\s+([\w.]+);', content)
            package_name = package_match.group(1) if package_match else "unknown"
            
            # Extract classes
            class_pattern = re.compile(r'(?:public|protected|private)?\s*(?:abstract)?\s*class\s+(\w+)(?:<[^>]+>)?(?:\s+extends\s+\w+(?:<[^>]+>)?)?(?:\s+implements\s+[^{]+)?{', re.DOTALL)
            for class_match in class_pattern.finditer(content):
                class_name = class_match.group(1)
                class_start = class_match.start()
                
                # Extract methods within the class
                self._extract_methods(content, class_name, package_name, file_path, class_start)
                
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")

    def _extract_methods(self, content: str, class_name: str, package_name: str, file_path: str, class_start: int) -> None:
        """
        Extract methods from a class definition.
        
        Args:
            content (str): File content
            class_name (str): Name of the current class
            package_name (str): Package name
            file_path (str): Path to the source file
            class_start (int): Position where the class definition starts
        """
        # Method regex: matches method signatures and captures groups for access, static, return type, name, params, exceptions
        method_pattern = re.compile(r'(public|protected|private)\s+(static\s+)?(\w+(?:<[^>]+>)?(?:\[\])?\s+)(\w+)\s*\((.*?)\)(?:\s+throws\s+([\w,\s]+))?\s*{', re.DOTALL)
        
        # Start searching from the beginning of the class
        for method_match in method_pattern.finditer(content[class_start:]):
            try:
                # Extract method details
                access = method_match.group(1)
                is_static = method_match.group(2) is not None
                return_type = method_match.group(3).strip()
                method_name = method_match.group(4)
                param_str = method_match.group(5)
                exceptions_str = method_match.group(6)
                
                # Skip methods that might be constructors
                if method_name == class_name:
                    continue
                
                # Calculate line number
                method_start_pos = class_start + method_match.start()
                line_number = content[:method_start_pos].count('\n') + 1
                
                # Parse parameters
                parameters = self._parse_parameters(param_str)
                
                # Parse exceptions
                exceptions = []
                if exceptions_str:
                    exceptions = [e.strip() for e in exceptions_str.split(',')]
                
                # Extract method body (for deeper analysis if needed)
                body_start = method_match.end()
                body = self._extract_method_body(content[class_start:], body_start)
                
                # Create and store the method object
                method = JavaMethod(
                    class_name=class_name,
                    package_name=package_name,
                    method_name=method_name,
                    access_modifier=access,
                    return_type=return_type,
                    parameters=parameters,
                    exceptions=exceptions,
                    is_static=is_static,
                    source_file=file_path,
                    line_number=line_number,
                    body=body
                )
                
                self.methods.append(method)
                
            except Exception as e:
                print(f"Error extracting method details in {file_path}: {e}")

    def _parse_parameters(self, param_str: str) -> List[Tuple[str, str]]:
        """
        Parse parameter list string into list of (type, name) tuples.
        
        Args:
            param_str (str): Parameter string from method signature
            
        Returns:
            List[Tuple[str, str]]: List of (type, name) tuples
        """
        params = []
        param_str = param_str.strip()
        
        if not param_str:
            return params
            
        # Split the parameters by commas, but be careful about generics
        in_generic = 0
        param_parts = []
        current_part = ""
        
        for char in param_str:
            if char == '<':
                in_generic += 1
            elif char == '>':
                in_generic -= 1
            elif char == ',' and in_generic == 0:
                param_parts.append(current_part)
                current_part = ""
                continue
            
            current_part += char
            
        if current_part:
            param_parts.append(current_part)
        
        # Process each parameter
        for part in param_parts:
            part = part.strip()
            if not part:
                continue
                
            # The last word is the parameter name, everything before is the type
            words = part.split()
            if len(words) >= 2:
                param_name = words[-1]
                param_type = ' '.join(words[:-1])
                params.append((param_type, param_name))
            else:
                # Handle the case where there might be no space between type and name
                print(f"Warning: Couldn't parse parameter {part} correctly. Assuming generic format.")
                params.append((part, "param"))
                
        return params

    def _extract_method_body(self, content: str, start_pos: int) -> str:
        """
        Extract the body of a method by balancing braces.
        
        Args:
            content (str): Content string starting from the class definition
            start_pos (int): Position where the method body starts (after the opening brace)
            
        Returns:
            str: Method body string
        """
        body = ""
        brace_level = 1
        i = start_pos
        
        # Simple brace matching to find the method body
        while i < len(content) and brace_level > 0:
            if content[i] == '{':
                brace_level += 1
            elif content[i] == '}':
                brace_level -= 1
            
            body += content[i]
            i += 1
            
        return body[:-1]  # Remove the last closing brace


def parse_java_repository(base_dir: str = None) -> List[JavaMethod]:
    """
    Parse the entire Java repository and return a list of methods.
    This is the main function to be used by other modules.
    
    Args:
        base_dir (str, optional): Base directory of the repository
        
    Returns:
        List[JavaMethod]: List of all methods found in the repository
    """
    parser = JavaParser(base_dir)
    return parser.parse_repository()


def get_method_dependencies(method: JavaMethod) -> List[str]:
    """
    Analyze a method's body to identify dependencies on other classes/methods.
    This is a simplified implementation and may not catch all dependencies.
    
    Args:
        method (JavaMethod): The method to analyze
        
    Returns:
        List[str]: List of dependent class names
    """
    dependencies = []
    
    # Look for new object instantiations
    new_pattern = re.compile(r'new\s+(\w+)')
    for match in new_pattern.finditer(method.body):
        dependencies.append(match.group(1))
    
    # Look for static method calls
    static_call_pattern = re.compile(r'(\w+)\.[\w<>]+\(')
    for match in static_call_pattern.finditer(method.body):
        if match.group(1) not in ['this', 'super'] and match.group(1)[0].isupper():
            dependencies.append(match.group(1))
    
    return list(set(dependencies))


def get_method_by_name(methods: List[JavaMethod], class_name: str, method_name: str) -> Optional[JavaMethod]:
    """
    Find a method by class and method name.
    
    Args:
        methods (List[JavaMethod]): List of methods to search in
        class_name (str): Name of the class
        method_name (str): Name of the method
        
    Returns:
        Optional[JavaMethod]: The found method or None
    """
    for method in methods:
        if method.class_name == class_name and method.method_name == method_name:
            return method
    return None


@dataclass
class MethodInfo:
    name: str
    parameters: List[Dict[str, Any]]
    return_type: str
    modifiers: List[str]
    body: str = ""


class JavaClassParser:
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Java file and return a dictionary containing:
         - package
         - class name
         - method details
         - import statements
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            package_name = tree.package.name if tree.package else ""
            class_type = next((t for t in tree.types if isinstance(t, javalang.tree.ClassDeclaration)), None)
            
            if not class_type:
                raise ValueError(f"No class definition found in {file_path}")
                
            class_name = class_type.name
            methods = self._extract_methods(class_type)
            imports = self._extract_imports(tree)
            
            return {
                "package": package_name,
                "class_name": class_name,
                "methods": methods,
                "imports": imports
            }
        except Exception as e:
            print(f"Error parsing Java file {file_path}: {str(e)}")
            raise
    
    def _extract_methods(self, class_type) -> List[MethodInfo]:
        """Extract method information from the class"""
        method_list = []
        if not class_type or not hasattr(class_type, 'methods'):
            return method_list
            
        for method in class_type.methods:
            try:
                params = []
                for param in method.parameters:
                    param_type = param.type.name if hasattr(param.type, 'name') else str(param.type)
                    params.append({
                        "name": param.name,
                        "type": param_type
                    })
                
                return_type = method.return_type.name if method.return_type else "void"
                modifiers = list(method.modifiers) if method.modifiers else []
                
                body = ""
                if method.body:
                    body = " ".join([str(statement) for statement in method.body])
                
                method_list.append(MethodInfo(
                    name=method.name,
                    parameters=params,
                    return_type=return_type,
                    modifiers=modifiers,
                    body=body
                ))
            except Exception as e:
                print(f"Error extracting method {method.name}: {str(e)}")
                continue
                
        return method_list
    
    def _extract_imports(self, tree) -> List[str]:
        """Extract import statements from the class"""
        imports = []
        if hasattr(tree, 'imports'):
            for imp in tree.imports:
                if hasattr(imp, 'path'):
                    imports.append(imp.path)
        return imports 