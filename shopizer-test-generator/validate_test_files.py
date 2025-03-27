#!/usr/bin/env python3
"""
Script to validate generated test files.
"""

import os
import re
import sys
from pathlib import Path


def find_test_files(directory):
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("Test.java"):
                test_files.append(os.path.join(root, file))
    return test_files


def validate_test_file_location(file_path):
    """Validate that the test file is in the correct location."""
    parts = Path(file_path).parts
    
    # Test file should be in src/test/java, not src/main/java
    if "main" in parts and "java" in parts:
        return False, f"Test file found in src/main/java instead of src/test/java: {file_path}"
    
    # Check for duplicate "test" directories
    if parts.count("test") > 1:
        return False, f"Test file found in nested test directories: {file_path}"
    
    return True, "Test file location is correct"


def validate_package_name(file_path):
    """Validate that the package name is correct."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract package declaration
        package_match = re.search(r'package\s+([\w.]+);', content)
        if not package_match:
            return False, f"No package declaration found in {file_path}"
        
        package_name = package_match.group(1)
        
        # Check for duplicate "test" segments in package name
        segments = package_name.split('.')
        if segments.count("test") > 0:
            return False, f"Package name contains 'test' segment: {package_name}"
        
        return True, "Package name is correct"
    except Exception as e:
        return False, f"Error checking package name: {str(e)}"


def validate_imports(file_path):
    """Validate that the imports are correct."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required imports
        required_imports = [
            "org.junit.jupiter.api.Test",
            "org.junit.jupiter.api.BeforeEach",
            "org.mockito.InjectMocks"
        ]
        
        missing_imports = []
        for imp in required_imports:
            pattern = rf'import\s+{imp};'
            if not re.search(pattern, content):
                missing_imports.append(imp)
        
        if missing_imports:
            return False, f"Missing required imports: {', '.join(missing_imports)}"
        
        return True, "Imports are correct"
    except Exception as e:
        return False, f"Error checking imports: {str(e)}"


def validate_test_file(file_path):
    """Validate a test file."""
    issues = []
    
    # Check file location
    location_valid, location_message = validate_test_file_location(file_path)
    if not location_valid:
        issues.append(location_message)
    
    # Check package name
    package_valid, package_message = validate_package_name(file_path)
    if not package_valid:
        issues.append(package_message)
    
    # Check imports
    imports_valid, imports_message = validate_imports(file_path)
    if not imports_valid:
        issues.append(imports_message)
    
    return issues


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_test_files.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        sys.exit(1)
    
    test_files = find_test_files(directory)
    print(f"Found {len(test_files)} test files")
    
    all_issues = {}
    for file_path in test_files:
        issues = validate_test_file(file_path)
        if issues:
            all_issues[file_path] = issues
    
    if all_issues:
        print("\nIssues found:")
        for file_path, issues in all_issues.items():
            print(f"\n{file_path}:")
            for issue in issues:
                print(f"  - {issue}")
        
        print(f"\nTotal files with issues: {len(all_issues)} out of {len(test_files)}")
        sys.exit(1)
    else:
        print("\nAll test files validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main() 