#!/usr/bin/env python3
"""
Main script for generating JUnit 5 test cases for Java methods using OpenAI API.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict

from src.generator.test_generator import TestGenerator
from src.utils.file_utils import validate_path, setup_test_paths
from src.utils.java_parser import JavaMethodParser


def main():
    """Main entry point for the test generator."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate JUnit 5 test cases for Java methods")
    parser.add_argument("source_dir", help="Directory containing Java source files")
    parser.add_argument("--test-dir", help="Directory for generated test files", default=None)
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY environment variable)", default=None)
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

    # Set OpenAI API key if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    elif not os.environ.get("OPENAI_API_KEY"):
        logging.error("OpenAI API key is required. Provide it with --api-key or set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    try:
        # Validate source directory or file
        source_dir = validate_path(args.source_dir)
        if not source_dir:
            logging.error(f"Invalid source directory or file: {args.source_dir}")
            sys.exit(1)
            
        # If the source is a single file, not a directory
        is_single_file = os.path.isfile(args.source_dir)
        if is_single_file:
            source_dir = os.path.dirname(args.source_dir)
            logging.info(f"Processing single file: {args.source_dir}")
        else:
            logging.info(f"Processing directory: {source_dir}")

        # Set up test directory
        test_dir = setup_test_paths(source_dir, args.test_dir)
        if not test_dir:
            logging.error("Failed to set up test directory")
            sys.exit(1)
            
        logging.info(f"Test files will be generated in: {test_dir}")

        # Find Java source files
        java_files = []
        if is_single_file:
            java_files = [args.source_dir]
        else:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.endswith(".java"):
                        java_files.append(os.path.join(root, file))

        if not java_files:
            logging.error(f"No Java files found in {source_dir}")
            sys.exit(1)

        logging.info(f"Found {len(java_files)} Java files")

        # Initialize test generator
        generator = TestGenerator(source_dir, test_dir)

        # Generate tests
        report = generator.generate_all_tests(java_files)

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

        logging.info("\nTest generation completed successfully")

    except Exception as e:
        logging.error(f"Error during test generation: {str(e)}")
        if args.verbose:
            logging.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    main() 