"""
Test generator module for generating test cases from Java source code.
"""

import os
import time
import re
from typing import List, Dict, Tuple, Optional, Set, Union, Any
import datetime
import logging
from ..models.test_to_code_model import TestToCodeModel
from src.parser.java_parser import JavaMethod, get_method_dependencies, MethodInfo
from src.utils.coverage_tracker import CoverageTracker


class TestGenerator:
    """
    Test generator class that handles the generation of test cases from Java source code.
    """
    
    def __init__(self, source_dir: str, test_dir: str):
        """
        Initialize the test generator.
        
        Args:
            source_dir (str): Directory containing source files
            test_dir (str): Directory where test files will be generated
        """
        self.source_dir = source_dir
        self.test_dir = test_dir
        self.test_model = TestToCodeModel()
        self.coverage_tracker = CoverageTracker()
        
        # Track generation metrics
        self.tested_methods: Set[str] = set()
        self.method_coverage: Dict[str, float] = {}
        self.generation_time: Dict[str, float] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.generated_tests: Dict[str, Set[str]] = {}  # Track generated tests per method

    def _get_test_path(self, source_file: str) -> str:
        """Convert source path to test path."""
        parts = source_file.split(os.sep)
        try:
            main_idx = parts.index("main")
            parts[main_idx] = "test"
            # Get the filename and add Test suffix before .java
            filename = parts[-1]
            base_name = os.path.splitext(filename)[0]
            parts[-1] = f"{base_name}Test.java"
            return os.sep.join(parts)
        except ValueError:
            base = os.path.splitext(source_file)[0]
            return f"{base}Test.java"

    def _get_package_name(self, source_file: str) -> str:
        """Extract package name from source file."""
        try:
            with open(source_file, 'r') as f:
                content = f.read()
            
            package_match = re.search(r'package\s+([\w.]+);', content)
            if package_match:
                return package_match.group(1)
        except Exception as e:
            logging.error(f"Error extracting package name: {str(e)}")
        
        return ''

    def _generate_test_class(self, test_file_path: str, method_info: List[Dict]) -> None:
        """Generate a test class file."""
        try:
            # Create test directory if it doesn't exist
            test_dir = os.path.join(os.path.dirname(test_file_path), 'test')
            os.makedirs(test_dir, exist_ok=True)
            
            # Use a simple file name based on the class name
            class_name = method_info[0]['class_name'] if isinstance(method_info, list) else 'Test'
            test_file = os.path.join(test_dir, f"{class_name}Test.java")
            
            # Generate test class content
            test_class_content = self._generate_test_class_content(method_info)
            
            # Write test class to file
            with open(test_file, 'w') as f:
                f.write(test_class_content)
                
            logging.info(f"Generated test class: {test_file}")
            
        except Exception as e:
            logging.error(f"Error generating test class: {str(e)}")
            raise

    def _format_test_code(self, test_code: str, method_name: str, test_type: str) -> str:
        """Format test code with proper structure and annotations."""
        # Clean up the test code
        test_code = test_code.strip()
        
        # Add method annotation and name
        formatted_test = [
            f"    @Test",
            f"    void test{method_name}_{test_type}() {{",
            "        // [MR1] - Testing method behavior",
            f"        // [M1, M2] - Ensuring {test_type.lower()} scenario coverage",
            ""
        ]
        
        # Add test code with proper indentation
        for line in test_code.split('\n'):
            formatted_test.append(f"        {line.strip()}")
        
        # Close method
        formatted_test.extend([
            "    }",
            ""
        ])
        
        return '\n'.join(formatted_test)

    def generate_all_tests(self, source_files: Union[List[str], Dict[str, str]]) -> Dict[str, Any]:
        """Generate tests for all methods in the source files."""
        total_methods = 0
        total_tests = 0
        start_time = time.time()
        
        if isinstance(source_files, list):
            # Process list of source files
            for source_file in source_files:
                try:
                    class_name, package_name, methods = self._parse_java_file(source_file)
                    if not methods:
                        continue
                        
                    test_cases = []
                    for method_name, method_code in methods.items():
                        try:
                            method_info = self._extract_method_info(method_name, method_code)
                            total_methods += 1
                            
                            for test_type in ['Positive', 'Negative', 'Edge']:
                                test_code = self.test_model.generate_test_case(method_info, test_type)
                                if test_code:
                                    test_cases.append(test_code)
                                    total_tests += 1
                                    
                        except Exception as e:
                            logging.error(f"Error generating tests for method {method_name}: {str(e)}")
                            continue
                    
                    if test_cases:
                        test_file_path = self._get_test_file_path(source_file)
                        self._generate_test_class(class_name, package_name, test_cases, test_file_path)
                        
                except Exception as e:
                    logging.error(f"Error processing file {source_file}: {str(e)}")
                    continue
        else:
            # Process dictionary of methods
            test_cases = []
            for method_name, method_code in source_files.items():
                try:
                    method_info = self._extract_method_info(method_name, method_code)
                    total_methods += 1
                    
                    for test_type in ['Positive', 'Negative', 'Edge']:
                        test_code = self.test_model.generate_test_case(method_info, test_type)
                        if test_code:
                            test_cases.append(test_code)
                            total_tests += 1
                            
                except Exception as e:
                    logging.error(f"Error generating tests for method {method_name}: {str(e)}")
                    continue
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / total_methods if total_methods > 0 else 0
        
        return {
            'total_methods': total_methods,
            'total_tests': total_tests,
            'total_time': total_time,
            'avg_time': avg_time
        }

    def _get_test_file_path(self, source_file: str) -> str:
        """Get the path for the test file."""
        source_dir = os.path.dirname(source_file)
        test_dir = os.path.join(source_dir, 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        file_name = os.path.basename(source_file)
        test_file_name = file_name.replace('.java', 'Test.java')
        return os.path.join(test_dir, test_file_name)

    def _extract_methods(self, content: str) -> List[Dict]:
        """Extract methods from Java source code."""
        methods = []
        
        # First get the class name
        class_match = re.search(r'public\s+class\s+(\w+)', content)
        if not class_match:
            return []
        
        class_name = class_match.group(1)
        
        # Find all method declarations, excluding constructors and inner classes
        method_pattern = r'(?:public|protected|private)\s+(?!class|interface|enum)(?!static\s+class)(?:\w+\s+)*(\w+)\s*\((.*?)\)(?:\s+throws\s+[\w,\s]+)?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        method_matches = re.finditer(method_pattern, content, re.DOTALL)
        
        for match in method_matches:
            method_name = match.group(1)
            
            # Skip if method name is a Java keyword or looks like a constructor
            if method_name in ['if', 'while', 'for', 'switch', 'try', 'catch'] or method_name == class_name:
                continue
            
            # Skip if method name is an exception type
            if method_name.endswith('Exception'):
                continue
            
            method_info = {
                'class_name': class_name,
                'name': method_name,
                'code': match.group(0),  # Full method including signature and body
                'parameters': [p.strip() for p in match.group(2).split(',') if p.strip()],
                'body': match.group(3).strip()
            }
            
            # Log found method
            logging.info(f"Found method: {method_info['name']}")
            methods.append(method_info)
        
        return methods

    def _group_methods_by_class(self, methods: List[Dict]) -> Dict[str, List[Dict]]:
        """Group methods by their class name."""
        grouped = {}
        for method in methods:
            class_name = method['class_name']
            if class_name not in grouped:
                grouped[class_name] = []
            grouped[class_name].append(method)
        return grouped

    def _analyze_dependencies(self, methods: List[Dict]) -> List[str]:
        """Analyze method dependencies."""
        dependencies = set()
        for method in methods:
            # Extract types from parameters
            for param in method['parameters']:
                param_type = param.split()[0]
                if not param_type.startswith(('int', 'long', 'boolean', 'String')):
                    dependencies.add(param_type)
            
            # Extract types from method body
            body = method['body']
            type_pattern = r'new\s+([A-Za-z_][A-Za-z0-9_]*)'
            for match in re.finditer(type_pattern, body):
                dependencies.add(match.group(1))
                
        return list(dependencies)

    def _generate_test_class_content(self, method_info: List[Dict]) -> str:
        """Generate the content of the test class."""
        if not method_info:
            return ""
            
        class_name = method_info[0]['class_name']
        
        # Generate imports
        imports = [
            "import org.junit.jupiter.api.Test;",
            "import org.junit.jupiter.api.BeforeEach;",
            "import org.junit.jupiter.api.extension.ExtendWith;",
            "import org.mockito.Mock;",
            "import org.mockito.InjectMocks;",
            "import org.mockito.junit.jupiter.MockitoExtension;",
            "import static org.junit.jupiter.api.Assertions.*;",
            "import static org.mockito.Mockito.*;"
        ]
        
        # Start class
        class_def = [
            "",
            "@ExtendWith(MockitoExtension.class)",
            f"public class {class_name}Test {{",
            "",
            "    @InjectMocks",
            f"    private {class_name} classUnderTest;",
            ""
        ]
        
        # Generate test methods for each method
        test_methods = []
        for method in method_info:
            # Generate test cases using the model
            test_cases = self.test_model.generate_test_cases(method['body'])
            test_methods.extend(test_cases)
        
        # Combine all parts
        content = "\n".join(imports + class_def + test_methods + ["}", ""])
        return content

    def _extract_method_info(self, method_name: str, method_code: str) -> Dict:
        """Extract method information from the code."""
        method_info = {
            'name': method_name,
            'return_type': 'void',  # Default
            'parameters': [],
            'exceptions': []
        }
        
        # Extract return type
        return_type_match = re.search(r'(public|private|protected)?\s+(\w+)\s+' + method_name, method_code)
        if return_type_match:
            method_info['return_type'] = return_type_match.group(2)
        
        # Extract parameters
        params_match = re.search(r'\((.*?)\)', method_code)
        if params_match:
            params = params_match.group(1).strip()
            if params:
                method_info['parameters'] = [p.strip() for p in params.split(',')]
        
        # Extract exceptions
        throws_match = re.search(r'throws\s+([\w,\s]+)', method_code)
        if throws_match:
            exceptions = throws_match.group(1).strip()
            method_info['exceptions'] = [e.strip() for e in exceptions.split(',')]
        
        return method_info

    def _parse_java_file(self, source_file: str) -> Tuple[str, str, Dict[str, str]]:
        """Parse a Java file and return its class name, package name, and methods."""
        with open(source_file, 'r') as f:
            content = f.read()
        
        # Extract methods
        methods = self._extract_methods(content)
        if not methods:
            return '', '', {}
        
        # Get class name from first method
        class_name = methods[0].get('class_name', '')
        if not class_name:
            return '', '', {}
        
        # Get package name
        package_name = self._get_package_name(source_file)
        
        # Convert methods list to dictionary
        method_dict = {}
        for method in methods:
            method_name = method.get('name', '')
            if method_name:
                method_dict[method_name] = method.get('body', '')
        
        return class_name, package_name, method_dict

    def _generate_test_class(self, class_name: str, package_name: str, test_cases: List[str], test_file_path: str) -> None:
        """Generate the test class file."""
        test_dir = os.path.join(os.path.dirname(test_file_path), 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        test_file_path = os.path.join(test_dir, f"{class_name}Test.java")
        
        template = self.test_model.get_test_class_template(
            package_name=f"{package_name}.test",
            class_name=class_name,
            test_cases=test_cases
        )
        
        with open(test_file_path, 'w') as f:
            f.write(template)
        
        logging.info(f"Generated test class: {test_file_path}")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_generator.py <source_file>")
        sys.exit(1)
        
    source_file = sys.argv[1]
    generator = TestGenerator()
    
    report = generator.generate_all_tests([source_file])
    
    logging.info("\nTest Generation Report:")
    logging.info(f"Total methods processed: {report['total_methods']}")
    logging.info(f"Total tests generated: {report['total_tests']}")
    logging.info(f"Total generation time: {report['total_time']:.2f} seconds")
    logging.info(f"Average time per method: {report['avg_time']:.2f} seconds") 