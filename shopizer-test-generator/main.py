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
from src.parser.java_parser import parse_java_repository
from src.generator.test_generator import generate_tests
from src.validators.coverage_validator import (
    simulate_test_execution,
    validate_coverage
)


def setup_test_file_path(source_file: str) -> tuple[str, str, str]:
    """
    Set up the test file path based on the source file location.
    
    Args:
        source_file (str): Path to the Java source file
        
    Returns:
        tuple[str, str, str]: Tuple containing (test_file_path, package_name, class_name)
    """
    # Ensure source file exists and is a Java file
    if not os.path.exists(source_file) or not source_file.endswith(".java"):
        print(f"Error: Invalid Java source file: {source_file}")
        sys.exit(1)
    
    # Extract the module path (path up to /src/)
    src_index = source_file.find("/src/")
    if src_index == -1:
        print(f"Error: Source file must be inside a /src/ directory: {source_file}")
        sys.exit(1)
    
    module_path = source_file[:src_index]
    
    # Get the relative path after /src/main/java/ or /src/
    java_base_path = "/src/main/java/"
    if java_base_path in source_file:
        relative_path = source_file[source_file.find(java_base_path) + len(java_base_path):]
    else:
        relative_path = source_file[src_index + 5:]  # +5 to skip "/src/"
    
    # Extract class name and package path
    class_name = os.path.splitext(os.path.basename(relative_path))[0]
    package_path = os.path.dirname(relative_path)
    package_name = package_path.replace("/", ".")
    
    # Construct test directory path
    test_dir = os.path.join(module_path, "src/test/java", package_path)
    test_file = os.path.join(test_dir, f"Test{class_name}.java")
    
    # Create test directory if it doesn't exist
    os.makedirs(test_dir, exist_ok=True)
    print(f"Test directory: {test_dir}")
    
    return test_file, package_name, class_name


def main() -> None:
    """
    Main entry point for the test generation process.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate tests for Shopizer")
    parser.add_argument(
        "--source", 
        required=True,
        help="Path to the Java source file"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=Config.REQUIRED_COVERAGE,
        help="Minimum required coverage percentage (0.0-1.0)"
    )
    args = parser.parse_args()
    
    # Print welcome message
    print("=" * 80)
    print("Shopizer Test Generator")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source file: {args.source}")
    print(f"Coverage threshold: {args.threshold:.1%}")
    print("-" * 80)
    
    # Start timing
    start_time = time.time()
    
    # Set up test file path and get package/class info
    test_file, package_name, class_name = setup_test_file_path(args.source)
    print(f"Generating test file: {test_file}")
    print(f"Package: {package_name}")
    print(f"Class: {class_name}")
    
    try:
        # Step 1: Parse the Java source file to extract method details
        print("\n=== Step 1: Parsing Java Source File ===")
        java_methods = parse_java_repository(args.source)
        print(f"Found {len(java_methods)} methods in {class_name}.")
        
        # Step 2: Generate Maven-compatible test cases for each method
        print("\n=== Step 2: Generating Test Cases ===")
        generation_report = generate_tests(java_methods, os.path.dirname(test_file))
        print(f"Generated {generation_report['total_tests_generated']} test cases.")
        print(f"Average generation time per method: {generation_report['average_generation_time_per_method']:.3f}s")
        
        # Step 3: Simulate test execution and validate coverage
        print("\n=== Step 3: Validating Test Coverage ===")
        coverage_data = simulate_test_execution(os.path.dirname(test_file))
        print(f"Average coverage: {coverage_data['average_coverage_percentage']:.2%}")
        print(f"Average pass rate: {coverage_data['average_pass_rate']:.2%}")
        
        # Check if coverage meets the threshold
        if validate_coverage(coverage_data, args.threshold):
            print("\n✅ Coverage threshold met.")
        else:
            print("\n⚠️ Coverage threshold not met. Some methods may need additional tests.")
        
        # Calculate and display execution time
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nTotal execution time: {total_time:.2f}s")
        
        # Print summary
        print("\n=== Test Generation Summary ===")
        print(f"Total methods analyzed: {len(java_methods)}")
        print(f"Total tests generated: {generation_report['total_tests_generated']}")
        print(f"Final coverage: {coverage_data['average_coverage_percentage']:.2%}")
        print(f"Final pass rate: {coverage_data['average_pass_rate']:.2%}")
        print(f"Methods below threshold: {coverage_data['methods_below_threshold']}")
        
        # Indicate success
        print("\n✅ Test generation complete.")
        print(f"Test file generated: {test_file}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during test generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 