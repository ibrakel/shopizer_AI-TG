"""
File utilities for path validation and setup.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import logging


def validate_path(path: str) -> Optional[str]:
    """
    Validate that a path exists and is readable.
    
    Args:
        path (str): Path to validate
        
    Returns:
        Optional[str]: Validated path, or None if invalid
    """
    if not path:
        return None
        
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return None
        
    if not os.path.isdir(path):
        path = os.path.dirname(path)
        
    return path


def setup_test_paths(source_dir: str, test_dir: Optional[str] = None) -> Optional[str]:
    """
    Set up test directory based on source directory.
    
    Args:
        source_dir (str): Source directory
        test_dir (Optional[str]): Optional test directory override
        
    Returns:
        Optional[str]: Test directory path, or None if setup failed
    """
    try:
        if test_dir:
            # Use provided test directory
            test_dir = os.path.abspath(test_dir)
        else:
            # Default: create test directory parallel to source
            source_path = Path(source_dir)
            source_parts = list(source_path.parts)
            
            # Check if this is a Maven-style project with main/java directory structure
            if "main" in source_parts and "java" in source_parts:
                # For Maven structure, replace 'main' with 'test' but keep the rest of the path
                main_index = source_parts.index("main")
                source_parts[main_index] = "test"
                test_dir = os.path.join(*source_parts)
                logging.info(f"Detected Maven structure. Test directory: {test_dir}")
            else:
                # Create test directory alongside source (non-Maven structure)
                test_dir = os.path.join(os.path.dirname(source_dir), "test")
                logging.info(f"Non-Maven structure. Test directory: {test_dir}")
        
        # Create test directory if it doesn't exist
        os.makedirs(test_dir, exist_ok=True)
        logging.info(f"Test directory set up at: {test_dir}")
        return test_dir
    except OSError as e:
        logging.error(f"Failed to set up test directory: {str(e)}")
        return None


def get_java_files(directory: str) -> List[str]:
    """
    Get all Java files in a directory recursively.
    
    Args:
        directory (str): Directory to search
        
    Returns:
        List[str]: List of Java file paths
    """
    java_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))
    return java_files


def get_test_file_path(source_file: str, test_dir: str) -> str:
    """
    Get the corresponding test file path for a source file.
    
    Args:
        source_file (str): Source file path
        test_dir (str): Test directory path
        
    Returns:
        str: Test file path
    """
    # Parse source file path
    source_parts = Path(source_file).parts
    
    # For Maven structure, maintain package hierarchy but change main to test
    if "main" in source_parts and "java" in source_parts:
        # Get the parts after "java" directory
        java_index = source_parts.index("java")
        package_path = os.path.join(*source_parts[java_index + 1:-1])
        
        # Get the filename and add Test suffix
        filename = source_parts[-1]
        base_name = os.path.splitext(filename)[0]
        test_filename = f"{base_name}Test.java"
        
        # Create full test path - make sure we don't duplicate the package path
        test_file_path = os.path.join(test_dir, package_path, test_filename)
        
        # Log the test file path for debugging
        logging.debug(f"Source file: {source_file}")
        logging.debug(f"Test file path: {test_file_path}")
        
        return test_file_path
    else:
        # For non-Maven structure, just replace the file extension
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        return os.path.join(test_dir, f"{base_name}Test.java")


def ensure_directory(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path
        
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError:
        return False


def copy_file_structure(source_dir: str, target_dir: str) -> bool:
    """
    Copy directory structure from source to target.
    
    Args:
        source_dir (str): Source directory
        target_dir (str): Target directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        for root, dirs, _ in os.walk(source_dir):
            # Get relative path
            relative_path = os.path.relpath(root, source_dir)
            
            # Create corresponding directories in target
            for dir_name in dirs:
                source_path = os.path.join(root, dir_name)
                target_path = os.path.join(target_dir, relative_path, dir_name)
                os.makedirs(target_path, exist_ok=True)
                
        return True
    except OSError:
        return False


def get_package_name(file_path: str) -> str:
    """
    Extract package name from a Java file path.
    
    Args:
        file_path (str): Path to Java file
        
    Returns:
        str: Package name
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for package declaration
        import re
        match = re.search(r'package\s+([\w.]+);', content)
        if match:
            package_name = match.group(1)
            logging.debug(f"Extracted package name from file: {package_name}")
            return package_name
    except (IOError, UnicodeDecodeError) as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        
    # If no package found or error occurred, derive from path
    parts = Path(file_path).parts
    if "java" in parts:
        java_index = parts.index("java")
        # Extract package parts after java directory, but before the file name
        package_parts = parts[java_index + 1:-1]
        # Join with dots to create a package name
        package_name = ".".join(package_parts)
        logging.debug(f"Derived package name from path: {package_name}")
        return package_name
    
    logging.warning(f"Could not determine package name for {file_path}")
    return ""


def get_class_name(file_path: str) -> str:
    """
    Extract class name from a Java file path.
    
    Args:
        file_path (str): Path to Java file
        
    Returns:
        str: Class name
    """
    # Get file name without extension
    base_name = os.path.basename(file_path)
    return os.path.splitext(base_name)[0]


def create_test_class_file(source_file: str, test_dir: str, content: str) -> bool:
    """
    Create a test class file for a source file.
    
    Args:
        source_file (str): Source file path
        test_dir (str): Test directory path
        content (str): Test class content
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get test file path
        test_file = get_test_file_path(source_file, test_dir)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        
        # Write test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True
    except (IOError, OSError):
        return False 