#!/usr/bin/env python3
"""
Main script for generating JUnit 5 test cases for Java methods using OpenAI API.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict
from pathlib import Path
import datetime

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
    parser.add_argument("--coverage-threshold", type=float, default=0.8,
                      help="Minimum coverage threshold (0.0-1.0)")
    parser.add_argument("--max-iterations", type=int, default=3,
                      help="Maximum iterations for coverage improvement")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("test_generation.log")
        ]
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

        # Initialize test generator with coverage threshold
        generator = TestGenerator(source_dir, test_dir, args.coverage_threshold)

        # Generate tests with coverage-based iteration
        report = generator.generate_all_tests(java_files, args.max_iterations)

        # Print detailed report
        logging.info("\nTest Generation Report:")
        logging.info("-" * 50)
        logging.info(f"Total files processed: {len(java_files)}")
        logging.info(f"Total methods processed: {report['total_methods']}")
        logging.info(f"Total tests generated: {report['tests_generated']}")
        logging.info(f"Total generation time: {report['total_time']:.2f} seconds")
        logging.info(f"Average time per method: {report['avg_time_per_method']:.2f} seconds")

        # Print coverage information
        logging.info("\nCoverage Report:")
        logging.info("-" * 50)
        below_threshold = []
        for method, coverage in report["method_coverage"].items():
            coverage_str = f"{coverage*100:.1f}%"
            status = "✓" if coverage >= args.coverage_threshold else "✗"
            logging.info(f"{status} {method}: {coverage_str}")
            if coverage < args.coverage_threshold:
                below_threshold.append((method, coverage))

        if below_threshold:
            logging.warning("\nMethods Below Coverage Threshold:")
            logging.warning("-" * 50)
            for method, coverage in below_threshold:
                logging.warning(f"{method}: {coverage*100:.1f}% (threshold: {args.coverage_threshold*100}%)")

        # Save report to file
        report_file = os.path.join(test_dir, "test_generation_report.txt")
        with open(report_file, "w") as f:
            f.write("Test Generation Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.datetime.now()}\n")
            f.write(f"Source directory: {source_dir}\n")
            f.write(f"Test directory: {test_dir}\n")
            f.write(f"Coverage threshold: {args.coverage_threshold*100}%\n")
            f.write(f"Maximum iterations: {args.max_iterations}\n\n")
            
            f.write("Summary\n")
            f.write("-" * 50 + "\n")
            f.write(f"Total files processed: {len(java_files)}\n")
            f.write(f"Total methods processed: {report['total_methods']}\n")
            f.write(f"Total tests generated: {report['tests_generated']}\n")
            f.write(f"Total generation time: {report['total_time']:.2f} seconds\n")
            f.write(f"Average time per method: {report['avg_time_per_method']:.2f} seconds\n\n")
            
            f.write("Coverage Details\n")
            f.write("-" * 50 + "\n")
            for method, coverage in sorted(report["method_coverage"].items()):
                status = "PASS" if coverage >= args.coverage_threshold else "FAIL"
                f.write(f"{status}: {method}: {coverage*100:.1f}%\n")

        logging.info(f"\nDetailed report saved to: {report_file}")
        logging.info("\nTest generation completed successfully")

    except KeyboardInterrupt:
        logging.info("\nTest generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error during test generation: {str(e)}")
        if args.debug:
            logging.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    main() 