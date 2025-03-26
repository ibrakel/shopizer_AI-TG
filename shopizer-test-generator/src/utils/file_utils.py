"""
File utilities for path validation and setup.
"""

import os
from typing import Optional


def validate_path(path: str) -> Optional[str]:
    """
    Validate if a path exists and is accessible.
    
    Args:
        path (str): Path to validate
        
    Returns:
        Optional[str]: Absolute path if valid, None otherwise
    """
    if not path:
        return None
        
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return None
        
    try:
        # Check if path is readable
        if os.path.isfile(abs_path):
            with open(abs_path, 'r') as _:
                pass
        else:
            os.listdir(abs_path)
        return abs_path
    except (IOError, OSError):
        return None


def setup_test_paths(source_dir: str, test_dir: Optional[str] = None) -> Optional[str]:
    """
    Set up test directory paths based on source directory.
    
    Args:
        source_dir (str): Source directory path
        test_dir (Optional[str]): Optional test directory path
        
    Returns:
        Optional[str]: Test directory path if setup successful, None otherwise
    """
    if not source_dir:
        return None
        
    # If test directory not specified, create parallel to source
    if not test_dir:
        source_parent = os.path.dirname(source_dir)
        test_dir = os.path.join(source_parent, "test")
    
    # Create test directory if it doesn't exist
    try:
        os.makedirs(test_dir, exist_ok=True)
        return test_dir
    except OSError:
        return None


def get_java_files(directory: str) -> list[str]:
    """
    Get all Java files in a directory recursively.
    
    Args:
        directory (str): Directory to search
        
    Returns:
        list[str]: List of Java file paths
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
    # Get relative path from source root
    source_root = os.path.dirname(os.path.dirname(source_file))
    relative_path = os.path.relpath(source_file, source_root)
    
    # Create test file path
    test_file = relative_path.replace(".java", "Test.java")
    return os.path.join(test_dir, test_file)


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
            return match.group(1)
    except (IOError, UnicodeDecodeError):
        pass
        
    # If no package found, derive from path
    parts = file_path.split(os.sep)
    if "java" in parts:
        java_index = parts.index("java")
        return ".".join(parts[java_index + 1:-1])
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