"""
Main module for Shopizer test generator.
This script provides the entry point for the test generation process.
"""

import os
import time
import argparse
import sys
from datetime import datetime
from config.settings import Config
from src.parser.java_parser import JavaClassParser
from src.generator.test_generator import TestGenerator
from src.validators.coverage_validator import CoverageValidator
from templates.test_templates import TestTemplates
from typing import Tuple


class DummyModelClient:
    def generate(self, prompt: str) -> str:
        return "// Generated test code by DummyModelClient"


def validate_file_path(file_path: str) -> bool:
    """
    Validate if the file exists and is a Java file
    """
    # Convert relative path to absolute path if needed
    abs_path = os.path.abspath(file_path)
    return os.path.isfile(abs_path) and file_path.endswith('.java')


def setup_test_file_path(source_file: str) -> Tuple[str, str, str]:
    """
    Create the test file path components from a source file path.
    Returns a tuple of (package_path, file_name, full_path)
    """
    abs_path = os.path.abspath(source_file)
    base_name = os.path.basename(abs_path)
    if base_name.endswith(".java"):
        test_name = base_name.replace(".java", "Test.java")
    else:
        test_name = base_name + "Test.java"
    
    dir_path = os.path.dirname(abs_path)
    package_path = dir_path.replace("src/main/java", "src/test/java")
    full_path = os.path.join(package_path, test_name)
    
    return package_path, test_name, full_path


def write_test_file(file_path: str, content: str) -> None:
    """Write the generated test content to a file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Test file written: {file_path}")


def process_single_file(file_path: str, coverage_threshold: float) -> None:
    """
    Process a single Java file and generate its test class
    """
    if not validate_file_path(file_path):
        print(f"Error: Invalid Java source file: {file_path}")
        print("Please ensure:")
        print("1. The file exists")
        print("2. The path is correct")
        print("3. The file has a .java extension")
        return

    parser = JavaClassParser()
    templates = TestTemplates()
    model_client = DummyModelClient()
    generator = TestGenerator(model_client, templates)
    validator = CoverageValidator()

    try:
        print(f"Processing file: {file_path}")
        # Parse the Java file
        class_info = parser.parse_file(file_path)
        # Generate test class code
        test_class_code = generator.generate_test_class(class_info)
        # Create test file path
        package_path, test_name, test_file_path = setup_test_file_path(file_path)
        # Write test file
        write_test_file(test_file_path, test_class_code)
        
        # Check coverage
        coverage = validator.check_coverage(test_file_path)
        print(f"Coverage for {test_file_path}: {coverage*100}%")
        if coverage < coverage_threshold:
            print(f"Warning: Coverage {coverage*100}% is below threshold {coverage_threshold*100}%")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Shopizer Test Generator')
    parser.add_argument('--source', required=True, help='Path to the Java source file')
    parser.add_argument('--threshold', type=float, default=0.9, help='Coverage threshold (default: 0.9)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Shopizer Test Generator")
    print("=" * 80)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source file: {args.source}")
    print(f"Coverage threshold: {args.threshold * 100}%")
    print("-" * 80)
    
    # Process the specified file
    process_single_file(args.source, args.threshold)


if __name__ == "__main__":
    main() 