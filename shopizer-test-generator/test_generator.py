#!/usr/bin/env python3
"""
Test script to verify the test generator functionality.
"""

import os
import sys
import logging
from src.generator.test_generator import TestGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def get_test_dir_from_source(source_file):
    """Convert source directory path to test directory path."""
    parts = source_file.split(os.sep)
    try:
        main_idx = parts.index("main")
        parts[main_idx] = "test"
        return os.sep.join(parts[:main_idx+1])
    except ValueError:
        return os.path.join(os.path.dirname(source_file), "test")

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        logging.error("Usage: python test_generator.py <path_to_java_file>")
        sys.exit(1)
        
    # Get source file path
    source_file = os.path.abspath(sys.argv[1])
    if not os.path.exists(source_file):
        logging.error(f"Source file not found: {source_file}")
        sys.exit(1)
    
    # Get source and test directories
    source_dir = os.path.dirname(source_file)
    test_dir = get_test_dir_from_source(source_file)
    
    # Create test generator
    generator = TestGenerator(source_dir, test_dir)
    
    # Generate tests
    logging.info(f"Generating tests for file: {source_file}")
    report = generator.generate_all_tests([source_file])
    
    # Print report
    logging.info("\nTest Generation Report:")
    logging.info(f"Total methods processed: {report['total_methods']}")
    logging.info(f"Total tests generated: {report['tests_generated']}")
    logging.info(f"Total generation time: {report['total_time']:.2f} seconds")
    logging.info(f"Average time per method: {report['avg_time_per_method']:.2f} seconds")
    
    # Print coverage information
    logging.info("\nCoverage Report:")
    for method, coverage in report["method_coverage"].items():
        logging.info(f"{method}: {coverage*100:.1f}%")

if __name__ == "__main__":
    main() 