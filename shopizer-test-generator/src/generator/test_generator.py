"""
Test generator module for generating test cases from Java source code.
"""

import os
import time
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Union, Any
import datetime
from ..models.test_to_code_model import TestToCodeModel
from ..utils.file_utils import get_package_name, get_test_file_path, ensure_directory
from ..parser.java_parser import JavaParser


class TestGenerator:
    """
    Test generator class that handles the generation of test cases from Java source code.
    """
    
    def __init__(self, source_dir: str, test_dir: str, coverage_threshold: float = 0.8):
        """
        Initialize the test generator.
        
        Args:
            source_dir (str): Directory containing source files
            test_dir (str): Directory where test files will be generated
            coverage_threshold (float): Minimum coverage threshold (0.0-1.0)
        """
        self.source_dir = source_dir
        self.test_dir = test_dir
        self.coverage_threshold = coverage_threshold
        self.test_model = TestToCodeModel()
        self.parser = JavaParser()
        
        # Track generation metrics
        self.tested_methods: Set[str] = set()
        self.method_coverage: Dict[str, float] = {}
        self.generation_time: Dict[str, float] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.generated_tests: Dict[str, Set[str]] = {}  # Track generated tests per method
        
        logging.info(f"Initialized Test Generator with source dir: {source_dir}")
        logging.info(f"Test files will be generated in: {test_dir}")
        logging.info(f"Coverage threshold set to: {coverage_threshold * 100}%")

    def _get_test_path(self, source_file: str) -> str:
        """
        Convert source path to test path.
        
        Args:
            source_file (str): Path to the source file
            
        Returns:
            str: Path to the corresponding test file
        """
        # Use the utility function to get the test file path
        return get_test_file_path(source_file, self.test_dir)

    def _get_package_name(self, source_file: str) -> str:
        """
        Extract package name from source file.
        
        Args:
            source_file (str): Path to the source file
            
        Returns:
            str: Package name extracted from the file
        """
        # Use the utility function to get the package name
        return get_package_name(source_file)

    def run_jacoco_analysis(self, test_file: str) -> Dict[str, float]:
        """
        Run tests and generate JaCoCo coverage report.
        
        Args:
            test_file (str): Path to the test file
            
        Returns:
            Dict[str, float]: Method coverage data
        """
        try:
            # Get project root (assuming Maven structure)
            project_root = os.path.dirname(os.path.dirname(self.source_dir))
            
            # Run Maven test with JaCoCo for specific test class
            test_class = os.path.splitext(os.path.basename(test_file))[0]
            cmd = f"cd {project_root} && ./mvnw test -Dtest={test_class} -DfailIfNoTests=false"
            logging.info(f"Running tests: {cmd}")
            
            os.system(cmd)
            
            # Parse JaCoCo report
            jacoco_report = os.path.join(project_root, "target/site/jacoco/index.html")
            if not os.path.exists(jacoco_report):
                logging.warning("JaCoCo report not found")
                return {}
                
            return self._parse_jacoco_report(jacoco_report)
            
        except Exception as e:
            logging.error(f"Error running JaCoCo analysis: {str(e)}")
            return {}

    def _parse_jacoco_report(self, report_path: str) -> Dict[str, float]:
        """
        Parse JaCoCo coverage report.
        
        Args:
            report_path (str): Path to JaCoCo report
            
        Returns:
            Dict[str, float]: Method coverage data
        """
        try:
            import xml.etree.ElementTree as ET
            
            # Convert HTML report path to XML report path
            xml_report = report_path.replace("index.html", "jacoco.xml")
            
            if not os.path.exists(xml_report):
                logging.warning(f"JaCoCo XML report not found: {xml_report}")
                return {}
                
            tree = ET.parse(xml_report)
            root = tree.getroot()
            
            coverage_data = {}
            
            # Parse method coverage from XML
            for package in root.findall(".//package"):
                for class_elem in package.findall("class"):
                    class_name = class_elem.get("name").replace("/", ".")
                    
                    for method in class_elem.findall("method"):
                        method_name = method.get("name")
                        counter = method.find("counter[@type='METHOD']")
                        
                        if counter is not None:
                            covered = int(counter.get("covered", 0))
                            missed = int(counter.get("missed", 0))
                            total = covered + missed
                            coverage = covered / total if total > 0 else 0
                            
                            full_name = f"{class_name}.{method_name}"
                            coverage_data[full_name] = coverage
            
            return coverage_data
            
        except Exception as e:
            logging.error(f"Error parsing JaCoCo report: {str(e)}")
            return {}

    def _generate_test_class(self, class_name: str, package_name: str, test_cases: List[str], source_file: str) -> str:
        """
        Generate a test class file.
        
        Args:
            class_name (str): Name of the class being tested
            package_name (str): Package name for the test class
            test_cases (List[str]): List of test case methods
            source_file (str): Source file path
            
        Returns:
            str: Path to the generated test file
        """
        try:
            # Get the test file path
            test_file_path = self._get_test_path(source_file)
            
            # Check for path issues - ensure we don't have duplicated package structure
            file_dir = os.path.dirname(test_file_path)
            package_parts = package_name.split('.')
            
            # Remove duplicate package structure if present
            current_parts = file_dir.split(os.sep)
            package_parts_in_path = [p for p in package_parts if p in current_parts]
            
            if len(package_parts_in_path) > len(set(package_parts_in_path)):
                # Remove duplicate package parts from path
                unique_parts = []
                seen = set()
                for part in current_parts:
                    if part not in package_parts or part not in seen:
                        unique_parts.append(part)
                        seen.add(part)
                        
                test_file_path = os.path.join(*unique_parts, f"{class_name}Test.java")
            
            # Ensure the directory exists
            test_dir = os.path.dirname(test_file_path)
            ensure_directory(test_dir)
            
            # Generate test class content
            test_class_content = self.test_model.get_test_class_template(
                package_name=package_name,
                class_name=class_name,
                test_cases=test_cases
            )
            
            # Write test class to file
            with open(test_file_path, 'w') as f:
                f.write(test_class_content)
                
            logging.info(f"Generated test class: {test_file_path}")
            return test_file_path
            
        except Exception as e:
            logging.error(f"Error generating test class: {str(e)}")
            raise

    def _format_test_code(self, test_code: str, method_name: str, test_type: str) -> str:
        """
        Format test code with proper structure and annotations.
        
        Args:
            test_code (str): Generated test code
            method_name (str): Name of the method being tested
            test_type (str): Type of test (Positive, Negative, Edge)
            
        Returns:
            str: Formatted test code
        """
        # Check if test_code is not a string (might be None or a dict)
        if not isinstance(test_code, str):
            logging.warning(f"Received non-string test code for {method_name}: {type(test_code)}")
            # Return a template test instead
            return f"""    @Test
    @DisplayName("{method_name} - {test_type} Test")
    void test{method_name}{test_type}() {{
        // [MR1] Testing method behavior
        // [M1] Code coverage
        // [M2] Assertion coverage
        
        // TODO: Implement test for {method_name}
        fail("Test not implemented");
    }}"""
            
        # Clean up the test code
        test_code = test_code.strip()
        
        # Remove any nested @Test annotations or duplicate method declarations
        nested_test_pattern = r'@Test[^{]*void\s+test\w+\([^)]*\)\s*\{'
        nested_matches = re.findall(nested_test_pattern, test_code)
        
        if len(nested_matches) > 1:
            # Keep only the first method declaration
            first_match = nested_matches[0]
            method_start = test_code.find(first_match)
            method_body_start = test_code.find('{', method_start) + 1
            method_body = test_code[method_body_start:]
            
            # Make sure to balance braces
            brace_count = 1
            for i, char in enumerate(method_body):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        method_body = method_body[:i]
                        break
            
            test_code = first_match + method_body
        
        # Fix common syntax issues
        # Ensure semicolons after statements
        test_code = re.sub(r'(\s*\w+\([^;{}]*\))\s*$', r'\1;', test_code)
        test_code = re.sub(r'(\s*\w+\([^;{}]*\))\s*\n', r'\1;\n', test_code)
        
        # Add method annotation and name
        formatted_test = [
            f"    @Test",
            f"    @DisplayName(\"{method_name} - {test_type} Test\")",
            f"    void test{method_name}{test_type}() {{"
        ]
        
        # Add test code with proper indentation
        inside_method = False
        for line in test_code.split('\n'):
            line = line.strip()
            # Skip @Test annotation, method signature, and existing DisplayName
            if '@Test' in line or '@DisplayName' in line or re.match(r'void\s+test\w+\s*\(', line):
                continue
                
            # If we encounter an opening brace, we're inside the method
            if '{' in line and not inside_method:
                inside_method = True
                continue
                
            # If we encounter a closing brace, we're at the end
            if line == '}' and inside_method:
                break
                
            # Add indentation to lines inside the method
            if inside_method and line:
                formatted_test.append(f"        {line}")
        
        # Ensure we have proper MR and M tags
        if not any('MR' in line for line in formatted_test):
            formatted_test.insert(3, f"        // [MR1] Testing {test_type.lower()} scenario")
            
        if not any('M1' in line for line in formatted_test):
            formatted_test.insert(4, f"        // [M1] Code coverage")
            formatted_test.insert(5, f"        // [M2] Assertion coverage")
            formatted_test.insert(6, "")
        
        # Close method
        formatted_test.append("    }")
        formatted_test.append("")
        
        # Ensure all statements end with semicolons
        result = '\n'.join(formatted_test)
        
        return result

    def _generate_template_test(self, method_info: dict, test_type: str) -> str:
        """
        Generate a template test when the API fails.
        
        Args:
            method_info (dict): Method information
            test_type (str): Type of test (Positive, Negative, Edge)
            
        Returns:
            str: Template test code
        """
        method_name = method_info["name"]
        parameters = method_info.get("parameters", [])
        return_type = method_info.get("return_type", "void")
        
        # Generate parameter setup
        param_lines = []
        param_names = []
        for param in parameters:
            parts = param.split()
            if len(parts) >= 2:
                param_type = parts[0]
                param_name = parts[-1]
                param_lines.append(f"{param_type} {param_name} = null; // Initialize with appropriate value")
                param_names.append(param_name)
        
        param_setup = "\n        ".join(param_lines) if param_lines else "// No parameters to set up"
        
        # Create method call with parameters
        method_call = f"classUnderTest.{method_name}({', '.join(param_names)})"
        
        # Generate assertion based on return type
        if return_type == "void":
            assertion = f"// Verify behavior of {method_name}\nfail(\"Test not implemented\");"
        else:
            assertion = f"{return_type} result = {method_call};\n        // Verify result\n        fail(\"Test not implemented\");"
        
        # Construct template based on test type
        if test_type == "Positive":
            description = "Test normal operation with valid inputs"
        elif test_type == "Negative":
            description = "Test error handling with invalid inputs"
        else:  # Edge
            description = "Test boundary conditions and edge cases"
        
        template = f"""// [MR1] {description}
// [M1] Code coverage metric
// [M2] Assertion completeness metric

// Arrange
{param_setup}

// Act
{assertion}"""
        
        return template

    def _generate_method_tests(self, method: 'JavaMethod') -> List[str]:
        """
        Generate test cases for a single method.
        
        Args:
            method (JavaMethod): Method to generate tests for
            
        Returns:
            List[str]: List of generated test cases
        """
        try:
            # Convert JavaMethod to dictionary format
            method_info = {
                'name': method.method_name,
                'class_name': method.class_name,
                'package': method.package_name,
                'return_type': method.return_type,
                'parameters': [f"{ptype} {pname}" for ptype, pname in method.parameters],
                'body': method.body,
                'is_static': method.is_static,
                'access_modifier': method.access_modifier,
                'exceptions': method.exceptions
            }
            
            # Generate test cases using the test model
            test_cases = self.test_model.generate_test_cases(method_info)
            
            # Track the generated tests
            if test_cases:
                method_key = method.get_qualified_name()
                if method_key not in self.generated_tests:
                    self.generated_tests[method_key] = set()
                self.generated_tests[method_key].update(test_cases)
                
            return test_cases
            
        except Exception as e:
            logging.error(f"Error generating tests for method {method.method_name}: {str(e)}")
            return []

    def _extract_method_body(self, content: str, line_number: int) -> str:
        """
        Extract method body from source code.
        
        Args:
            content (str): Source file content
            line_number (int): Line number where the method starts
            
        Returns:
            str: Method body
        """
        try:
            lines = content.splitlines()
            if line_number > len(lines):
                return ""
                
            # Find method start (opening brace)
            start_line = line_number - 1
            while start_line < len(lines) and '{' not in lines[start_line]:
                start_line += 1
                
            if start_line >= len(lines):
                return ""
                
            # Find method end (matching closing brace)
            brace_count = 0
            end_line = start_line
            
            for i in range(start_line, len(lines)):
                line = lines[i]
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0:
                    end_line = i
                    break
                    
            # Extract and return the method body
            body_lines = lines[start_line:end_line + 1]
            return '\n'.join(body_lines)
            
        except Exception as e:
            logging.error(f"Error extracting method body: {str(e)}")
            return ""

    def generate_all_tests(self, source_files: List[str]) -> Dict[str, Any]:
        """
        Generate tests for all methods in the given source files.
        
        Args:
            source_files (List[str]): List of source files to process
            
        Returns:
            Dict[str, Any]: Generation report
        """
        start_time = time.time()
        total_methods = 0
        tests_generated = 0
        
        logging.info(f"Found {len(source_files)} Java files")
        
        for source_file in source_files:
            try:
                logging.info(f"\nProcessing file: {source_file}")
                
                # Parse the file
                self.parser._parse_file(source_file)
                methods = self.parser.methods
                
                if not methods:
                    logging.warning("No methods found after parsing source file")
                    continue
                
                # Get class and package names from the first method
                class_name = methods[0].class_name
                package_name = methods[0].package_name
                
                # Generate tests for each method
                test_cases = []
                for method in methods:
                    total_methods += 1
                    
                    # Get method body if not already present
                    if not method.body:
                        with open(source_file, 'r') as f:
                            content = f.read()
                            method.body = self._extract_method_body(content, method.line_number)
                    
                    # Generate test cases
                    method_tests = self._generate_method_tests(method)
                    if method_tests:
                        test_cases.extend(method_tests)
                        tests_generated += len(method_tests)
                    else:
                        logging.warning(f"No tests generated for method: {method.method_name}")
                
                if test_cases:
                    # Generate test class file
                    test_file = self._generate_test_class(class_name, package_name, test_cases, source_file)
                    
                    # Run coverage analysis
                    coverage = self.run_jacoco_analysis(test_file)
                    self.method_coverage.update(coverage)
                else:
                    logging.warning(f"No tests generated for file: {source_file}")
                    
            except Exception as e:
                logging.error(f"Error processing file {source_file}: {str(e)}")
                continue
        
        # Calculate metrics
        total_time = time.time() - start_time
        avg_time = total_time / total_methods if total_methods > 0 else 0
        
        return {
            "total_methods": total_methods,
            "tests_generated": tests_generated,
            "total_time": total_time,
            "avg_time_per_method": avg_time,
            "method_coverage": self.method_coverage
        }

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
    logging.info(f"Total tests generated: {report['tests_generated']}")
    logging.info(f"Total generation time: {report['total_time']:.2f} seconds")
    logging.info(f"Average time per method: {report['avg_time_per_method']:.2f} seconds") 