# Shopizer Test Generator with OpenAI Integration

This package generates JUnit 5 test cases for Java methods using OpenAI's API.

## Installation

1. Clone the repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Environment Setup

Set your OpenAI API key in one of the following ways:

1. As an environment variable:
```bash
export OPENAI_API_KEY=your_api_key_here
```

2. Pass it as a command-line argument when running the tool:
```bash
python main.py /path/to/java/source --api-key your_api_key_here
```

## Usage

```bash
python main.py /path/to/java/source [--test-dir /path/to/output] [--api-key your_api_key_here] [--verbose]
```

Arguments:
- `source_dir`: Directory containing Java source files (required)
- `--test-dir`: Directory for generated test files (optional, defaults to source_dir/test)
- `--api-key`: OpenAI API key (optional if already set as environment variable)
- `--verbose`: Enable verbose output

## Test API Script

For testing the API connection and generation capabilities:

```bash
python test_api.py
```

This script will:
1. Test the prompt generation
2. Test the code generation pipeline
3. Test error handling mechanisms

## Features

- Generates JUnit 5 test cases for Java methods
- Uses OpenAI's API to generate test implementations
- Supports positive, negative, and edge case test generation
- Includes appropriate assertion statements and mocks
- Generates test class files with proper imports and setup
- Tracks generation metrics and provides reporting

## Requirements

- Python 3.7+
- OpenAI API key
- Java code to test (source files) 