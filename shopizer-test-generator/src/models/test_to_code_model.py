"""
Test-to-code model implementation using OpenAI's API endpoint.
This module provides functionality to generate test cases from source code.
"""

import os
import requests
from typing import List, Dict, Optional
import logging
import re
import datetime
import json
import time
import openai

class TestToCodeModel:
    """
    A model that generates test cases from source code using OpenAI's API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the test-to-code model.
        
        Args:
            api_key (str, optional): OpenAI API key (defaults to environment variable)
        """
        # Get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        # Configure OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Initialize error tracking
        self.error_stats = {
            'api_errors': [],
            'extraction_errors': [],
            'validation_errors': [],
            'generation_attempts': 0,
            'successful_generations': 0
        }
        
        # Initialize feedback tracking
        self.feedback_data = {
            'prompt_success_rate': {},  # Track success rate per prompt type
            'error_patterns': set(),    # Track common error patterns
            'complex_methods': set()    # Track methods that needed multiple attempts
        }
        
        try:
            # Test the connection
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test generation assistant."},
                    {"role": "user", "content": "test connection"}
                ],
                max_tokens=50
            )
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                logging.info("Connected to OpenAI API successfully")
            else:
                logging.warning("Connection test returned an unexpected response format")
        except Exception as e:
            logging.error(f"Failed to connect to OpenAI API: {str(e)}")
            raise

    def _create_prompt(self, method_info: Dict, test_type: str) -> str:
        """
        Create a dynamic prompt based on method complexity and characteristics.
        
        Args:
            method_info (Dict): Method information including name, parameters, etc.
            test_type (str): Type of test to generate (Positive/Negative/Edge)
            
        Returns:
            str: Generated prompt
        """
        test_type_focus = {
            'Positive': 'Test valid inputs and expected behavior',
            'Negative': 'Test error handling and invalid inputs',
            'Edge': 'Test boundary conditions and extreme values'
        }
        
        # Create a concise prompt
        return f"""Generate EXACTLY ONE test method with this structure:

@Test
@DisplayName("{method_info['name']} - {test_type} Test")
void test{method_info['name']}{test_type}() {{
    // [MR1] Testing {test_type.lower()} scenario
    // [M1] Code coverage
    // [M2] Assertion coverage
    
    // Your implementation here
}}

Method details:
- Name: {method_info['name']}
- Return: {method_info['return_type']}
- Params: {', '.join(method_info.get('parameters', []))}
- Focus: {test_type_focus.get(test_type, '')}

IMPORTANT: Generate ONLY the test method. DO NOT write anything else."""

    def _parse_api_response(self, response_json) -> Optional[str]:
        """Parse the API response and extract the generated text.
        
        Args:
            response_json: Raw API response
            
        Returns:
            Optional[str]: The generated text if found, None otherwise
        """
        try:
            # Log the raw response for debugging
            logging.debug(f"Raw API response: {response_json}")
            
            # Extract generated text from response
            if isinstance(response_json, dict):
                generated_text = response_json.get('generated_text')
                if generated_text:
                    return generated_text
                    
            logging.warning("Could not find generated_text in API response")
            return None
            
        except Exception as e:
            logging.error(f"Error parsing API response: {str(e)}")
            return None

    def _extract_code_block(self, content: str) -> Optional[str]:
        """
        Extract code block from message content using multiple strategies.
        
        Args:
            content (str): Message content containing code
            
        Returns:
            Optional[str]: Extracted code block if found, None otherwise
        """
        if not content:
            return None
        
        try:
            # Log the content for debugging
            logging.debug(f"Attempting to extract code from content:\n{content}")
            
            # Strategy 1: Look for complete test method with annotations
            test_pattern = r'@Test\s*(?:@DisplayName\s*\([^)]+\)\s*)?void\s+test\w+\s*\(\s*\)\s*\{[^}]*\}'
            matches = re.findall(test_pattern, content, re.DOTALL)
            
            if matches:
                logging.debug("Found code block using Strategy 1")
                return matches[0].strip()
            
            # Strategy 2: Look for content between code block markers
            code_pattern = r'```(?:java)?\s*(.*?)```'
            matches = re.findall(code_pattern, content, re.DOTALL)
            
            for match in matches:
                # Only use the match if it contains a test method
                if '@Test' in match and 'void test' in match:
                    logging.debug("Found code block using Strategy 2")
                    return match.strip()
            
            # Strategy 3: Look for test method without annotations
            method_pattern = r'void\s+test\w+\s*\(\s*\)\s*\{[^}]*\}'
            matches = re.findall(method_pattern, content, re.DOTALL)
            
            if matches:
                # Add required annotations if missing
                test_code = matches[0].strip()
                if not test_code.startswith('@Test'):
                    test_code = '@Test\n' + test_code
                logging.debug("Found code block using Strategy 3")
                return test_code
            
            # Strategy 4: Extract any content that looks like a test method
            test_indicators = [
                r'@Test',
                r'void\s+test\w+',
                r'\[MR\d+\]',
                r'assert[A-Z]\w+\(',
                r'verify\('
            ]
            
            # Find the earliest occurrence of any indicator
            start_pos = len(content)
            for pattern in test_indicators:
                match = re.search(pattern, content)
                if match and match.start() < start_pos:
                    start_pos = match.start()
            
            if start_pos < len(content):
                # Extract from the earliest indicator to the end
                partial_content = content[start_pos:]
                # Try to find a balanced block
                test_code = self._extract_balanced_block(partial_content)
                if test_code and '@Test' in test_code:
                    logging.debug("Found code block using Strategy 4")
                    return test_code
            
            logging.warning("No code block found using any extraction strategy")
            logging.debug("Content that failed extraction:\n" + content)
            return None
            
        except Exception as e:
            logging.error(f"Error extracting code block: {str(e)}")
            logging.debug(f"Problematic content:\n{content}")
            return None

    def _extract_balanced_block(self, text: str) -> str:
        """
        Extract a balanced code block with matching braces.
        
        Args:
            text (str): Text containing code block
            
        Returns:
            str: Balanced code block
        """
        try:
            # First, try to find a complete test method
            test_start = text.find("@Test")
            if test_start == -1:
                test_start = text.find("void test")
            
            if test_start == -1:
                return text.strip()
                
            # Look for the opening brace
            brace_start = text.find("{", test_start)
            if brace_start == -1:
                return text.strip()
            
            # Track brace balance
            stack = []
            result = []
            in_block = False
            
            for i, char in enumerate(text):
                if i < test_start:
                    continue
                    
                if char == "{":
                    stack.append(char)
                    in_block = True
                elif char == "}":
                    if stack:
                        stack.pop()
                    if not stack and in_block:
                        result.append(char)
                        break
                
                if in_block or i <= brace_start:
                    result.append(char)
            
            extracted = "".join(result).strip()
            
            # If we don't have a complete block, return the original text
            if not extracted or "{" not in extracted or "}" not in extracted:
                return text.strip()
                
            return extracted
            
        except Exception as e:
            logging.error(f"Error in _extract_balanced_block: {str(e)}")
            return text.strip()

    def _extract_test_code(self, response_json):
        """Extract test code from API response.
        
        Args:
            response_json (dict): API response containing generated text
            
        Returns:
            str: Extracted test code or None if no code found
        """
        try:
            # Parse the API response to get the assistant's message
            content = self._parse_api_response(response_json)
            if not content:
                logging.warning(f"No content found in API response (ID: {response_json.get('request_id', 'unknown')})")
                return None

            # First try to extract content between response tags
            response_pattern = r"<response>(.*?)</response>"
            response_match = re.search(response_pattern, content, re.DOTALL)
            if response_match:
                content = response_match.group(1).strip()
                
            # Extract code block from the content
            test_code = self._extract_code_block(content)
            if not test_code:
                logging.warning(f"No test code found in content (ID: {response_json.get('request_id', 'unknown')})")
                return None
                
            # Clean and validate the test code
            test_code = self._clean_generated_code(test_code)
            
            # Validate the test code structure
            if not self._is_valid_test_code(test_code):
                logging.warning(f"Generated code is not a valid test (ID: {response_json.get('request_id', 'unknown')})")
                return None
                
            # Log the extracted test code for debugging
            debug_dir = "debug_output"
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            request_id = response_json.get('request_id', 'unknown')
            debug_file = os.path.join(debug_dir, f"test_code_{timestamp}_{request_id}.txt")
            
            with open(debug_file, "w", encoding='utf-8') as f:
                f.write(f"=== Extracted Test Code (ID: {request_id}) ===\n")
                f.write(test_code)
                f.write("\n")
            
            return test_code
            
        except Exception as e:
            request_id = response_json.get('request_id', 'unknown')
            logging.error(f"Error extracting test code (ID: {request_id}): {str(e)}")
            return None

    def _clean_generated_code(self, code: str) -> str:
        """Clean up the generated code."""
        # Remove line numbers and colons
        code = re.sub(r'^\d+:\s*', '', code, flags=re.MULTILINE)
        
        # Fix indentation
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove any explicit indentation numbers
            line = re.sub(r'^\d+\s+', '', line)
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def _is_valid_test_code(self, code: str) -> bool:
        """
        Validate the structure and content of generated test code.
        
        Args:
            code (str): Generated test code
            
        Returns:
            bool: True if code appears to be valid test code
        """
        if not code:
            return False
            
        # Required elements with more flexible pattern matching
        required_patterns = [
            (r"@Test", "Missing @Test annotation"),
            (r"void\s+test\w+\s*\(", "Invalid test method signature"),
            (r"assert|verify|when|mock", "Missing assertions or verifications")
            # Removed requirement for tags as OpenAI is inconsistent with them
        ]
        
        # Track which patterns are found
        found_patterns = {pattern: False for pattern, _ in required_patterns}
        
        # Check each line for patterns
        for line in code.split('\n'):
            for pattern, _ in required_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found_patterns[pattern] = True
        
        # Check if we found at least one of each required pattern
        missing_patterns = []
        for pattern, message in required_patterns:
            if not found_patterns[pattern]:
                logging.warning(f"Validation failed: {message}")
                missing_patterns.append(message)
        
        if missing_patterns:
            return False
        
        # Check basic structure
        try:
            # Count braces to ensure they're balanced
            if code.count('{') != code.count('}'):
                logging.warning("Validation failed: Unbalanced braces")
                return False
            
            # Check for common syntax errors - removed the empty method call check
            error_patterns = [
                r";\s*;",  # Double semicolon
                r"\{\s*\}",  # Empty block
                r"return\s*;[^}]"  # Premature return
                # Removed the problematic \(\s*\)\s*; pattern
            ]
            
            for pattern in error_patterns:
                if re.search(pattern, code):
                    logging.warning(f"Validation failed: Found syntax error pattern: {pattern}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error during test code validation: {str(e)}")
            return False

    def generate_test_cases(self, method_code: str) -> List[str]:
        """
        Generate test cases for a given method.
        
        Args:
            method_code (str): Source code of the method to test
            
        Returns:
            List[str]: Generated test cases (positive, negative, edge)
        """
        test_cases = []
        method_info = self._extract_method_info(method_code)
        
        if not method_info:
            logging.warning("Could not extract method information")
            return []

        # Create debug directory if it doesn't exist
        debug_dir = "debug_output"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Create a timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        for test_type in ["Positive", "Negative", "Edge"]:
            max_attempts = 3
            attempt = 1
            success = False
            
            while attempt <= max_attempts and not success:
                try:
                    prompt = self._create_prompt(method_info, test_type)
                    
                    # Create debug file for this attempt
                    debug_file = os.path.join(
                        debug_dir, 
                        f'{method_info["name"]}_{test_type}_{timestamp}_attempt{attempt}.txt'
                    )
                    
                    with open(debug_file, 'w') as f:
                        f.write(f'Method: {method_info["name"]}\n')
                        f.write(f'Test Type: {test_type}\n')
                        f.write(f'Attempt: {attempt}\n\n')
                    
                    # Make API request
                    response = self._call_api(prompt)
                    
                    if response:
                        # Extract test code from response
                        test_code = self._extract_test_code(response)
                        
                        if test_code:
                            # Save extracted test code
                            with open(debug_file, 'a') as f:
                                f.write('\n=== Generated Test Code ===\n')
                                f.write(test_code)
                                f.write('\n')
                            
                            test_cases.append(test_code)
                            success = True
                            logging.info(f'Successfully generated {test_type} test for {method_info["name"]}')
                        else:
                            logging.warning(f'No test code extracted for {method_info["name"]} ({test_type}), attempt {attempt}')
                            with open(debug_file, 'a') as f:
                                f.write('\n=== Extraction Failed ===\n')
                                f.write('Could not extract test code from response\n')
                    else:
                        logging.warning(f'API response was empty for {method_info["name"]} ({test_type}), attempt {attempt}')
                        
                except Exception as e:
                    logging.error(f'Error generating {test_type} test (attempt {attempt}): {str(e)}')
                    with open(debug_file, 'a') as f:
                        f.write('\n=== Error ===\n')
                        f.write(f'Error: {str(e)}\n')
                
                attempt += 1
                
            if not success:
                # If all attempts failed, use a template
                template_code = self._generate_template_test(method_info, test_type)
                test_cases.append(template_code)
                
                # Save template fallback
                with open(debug_file, 'a') as f:
                    f.write('\n=== Template Fallback ===\n')
                    f.write('Using template test code after all attempts failed\n')
                    f.write(template_code)
                    f.write('\n')

        return test_cases

    def _generate_template_test(self, method_info: Dict, test_type: str) -> str:
        """Generate a template test when model generation fails."""
        method_name = method_info['name']
        param_list = method_info['parameters']
        return_type = method_info['return_type']
        
        # Generate parameter setup code
        param_setup = []
        param_names = []
        for param in param_list:
            parts = param.split()
            if len(parts) >= 2:
                param_type = parts[0]
                param_name = parts[-1]
                param_setup.append(f"        {param_type} {param_name} = null; // TODO: Initialize parameter")
                param_names.append(param_name)
        
        # Generate method call
        method_call = f"classUnderTest.{method_name}({', '.join(param_names)})"
        
        # Generate assertion based on return type
        if return_type == 'void':
            assertion = "        // TODO: Verify void method behavior"
        else:
            assertion = f"        {return_type} result = {method_call};\n        // TODO: Add assertions for result"
        
        template = f"""    @Test
    void test{method_name}_{test_type}() {{
        // [MR1] - Testing method behavior
        // [M1, M2] - Ensuring {test_type.lower()} scenario coverage
        
        // Arrange
{chr(10).join(param_setup) if param_setup else '        // TODO: Setup test data and mocks'}
        
        // Act
        {assertion if return_type == 'void' else f'        {return_type} result = {method_call};'}
        
        // Assert
        {'// TODO: Add assertions to verify the behavior' if return_type == 'void' else '// TODO: Add assertions for result'}
        fail("Test not implemented");
    }}"""
        return template

    def _extract_method_info(self, code: str) -> Dict:
        """
        Extract method information from code.
        
        Args:
            code (str): Source code of the method
            
        Returns:
            Dict: Method information including name, parameters, and return type
        """
        # Extract method signature
        method_pattern = r'(?:public|private|protected)?\s+(?:static\s+)?(\w+)\s+(\w+)\s*\((.*?)\)'
        match = re.search(method_pattern, code)
        
        if not match:
            return {}
            
        # Clean up method name (remove 'if' if it's just a placeholder)
        method_name = match.group(2)
        if method_name == 'if':
            # Try to extract class name to get actual method name
            class_match = re.search(r'class\s+(\w+)', code)
            if class_match:
                class_name = class_match.group(1)
                if class_name.endswith('Impl'):
                    # Remove 'Impl' and use first method from interface
                    interface_name = class_name[:-4]
                    method_name = f"get{interface_name}"
            
        return {
            'return_type': match.group(1),
            'name': method_name,
            'parameters': [p.strip() for p in match.group(3).split(',') if p.strip()]
        }

    def get_required_imports(self, test_code: str) -> List[str]:
        """Extract required imports from generated test code."""
        imports = set()
        
        # Common test imports
        imports.add("org.junit.jupiter.api.Test")
        imports.add("org.junit.jupiter.api.BeforeEach")
        imports.add("static org.junit.jupiter.api.Assertions.*")
        
        # Check for Mockito usage
        if "mock(" in test_code.lower() or "@mock" in test_code.lower():
            imports.add("org.mockito.Mock")
            imports.add("org.mockito.InjectMocks")
            imports.add("org.mockito.junit.jupiter.MockitoExtension")
            imports.add("static org.mockito.Mockito.*")
            
        return sorted(list(imports))

    def generate_test_case(self, method_info: Dict, test_type: str) -> Optional[str]:
        """
        Generate a test case with enhanced error handling and feedback.
        
        Args:
            method_info (Dict): Method information
            test_type (str): Type of test to generate
            
        Returns:
            Optional[str]: Generated test code if successful
        """
        self.error_stats['generation_attempts'] += 1
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Create prompt
                prompt = self._create_prompt(method_info, test_type)
                
                # Call API
                response = self._call_api(prompt)
                if not response:
                    self._log_error('api', 'No response from API', method_info['name'])
                    continue
                
                # Extract test code
                test_code = self._extract_test_code(response)
                if not test_code:
                    self._log_error('extraction', 'Failed to extract test code', method_info['name'])
                    continue
                
                # Validate test code
                if not self._is_valid_test_code(test_code):
                    self._log_error('validation', 'Invalid test code structure', method_info['name'])
                    continue
                
                # Success
                self.error_stats['successful_generations'] += 1
                self._update_feedback_loop(method_info, True)
                return test_code
                
            except Exception as e:
                self._log_error('generation', str(e), method_info['name'])
                
            # Update feedback loop with failure
            self._update_feedback_loop(method_info, False, f'attempt_{attempt+1}_failed')
            
            # Adjust prompt based on failure type
            if attempt < max_attempts - 1:
                logging.info(f"Retrying with adjusted prompt for {method_info['name']}")
        
        # All attempts failed
        logging.error(f"Failed to generate test case for {method_info['name']} after {max_attempts} attempts")
        return None

    def _log_error(self, error_type: str, details: str, method_name: str = None):
        """Log an error and update error statistics."""
        timestamp = datetime.datetime.now().isoformat()
        error_entry = {
            'timestamp': timestamp,
            'type': error_type,
            'details': details,
            'method': method_name
        }
        
        if error_type == 'api':
            self.error_stats['api_errors'].append(error_entry)
        elif error_type == 'extraction':
            self.error_stats['extraction_errors'].append(error_entry)
        elif error_type == 'validation':
            self.error_stats['validation_errors'].append(error_entry)
            
        # Write to error log file
        log_dir = "debug_output/errors"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"error_log_{datetime.datetime.now().strftime('%Y%m%d')}.json")
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
                
            logs.append(error_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to write to error log: {str(e)}")

    def _update_feedback_loop(self, method_info: Dict, success: bool, error_type: str = None):
        """Update feedback data for prompt optimization."""
        method_name = method_info['name']
        complexity = 'complex' if len(method_info.get('parameters', [])) > 2 else 'simple'
        
        # Update prompt success rate
        if complexity not in self.feedback_data['prompt_success_rate']:
            self.feedback_data['prompt_success_rate'][complexity] = {'success': 0, 'total': 0}
            
        self.feedback_data['prompt_success_rate'][complexity]['total'] += 1
        if success:
            self.feedback_data['prompt_success_rate'][complexity]['success'] += 1
            
        # Track complex methods needing multiple attempts
        if not success and complexity == 'complex':
            self.feedback_data['complex_methods'].add(method_name)
            
        # Track error patterns
        if error_type:
            self.feedback_data['error_patterns'].add(error_type)
            
        # Save feedback data
        self._save_feedback_data()

    def _save_feedback_data(self):
        """Save feedback data to file for analysis."""
        feedback_dir = "debug_output/feedback"
        os.makedirs(feedback_dir, exist_ok=True)
        
        feedback_file = os.path.join(feedback_dir, "feedback_data.json")
        try:
            data = {
                'prompt_success_rate': self.feedback_data['prompt_success_rate'],
                'error_patterns': list(self.feedback_data['error_patterns']),
                'complex_methods': list(self.feedback_data['complex_methods']),
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            with open(feedback_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to save feedback data: {str(e)}")

    def get_test_class_template(self, package_name: str, class_name: str, test_cases: List[str]) -> str:
        """Generate a test class template."""
        imports = [
            f"package {package_name};",
            "",
            "import org.junit.jupiter.api.Test;",
            "import org.junit.jupiter.api.DisplayName;",
            "import org.junit.jupiter.api.BeforeEach;",
            "import org.mockito.Mock;",
            "import org.mockito.InjectMocks;",
            "import org.mockito.MockitoAnnotations;",
            "import static org.mockito.Mockito.*;",
            "import static org.junit.jupiter.api.Assertions.*;",
            "",
            f"class {class_name}Test {{",
            "",
            "    @InjectMocks",
            f"    private {class_name} classUnderTest;",
            "",
            "    @BeforeEach",
            "    void setUp() {",
            "        MockitoAnnotations.openMocks(this);",
            "    }",
            ""
        ]
        
        test_methods = []
        for test_case in test_cases:
            test_methods.extend(["", test_case])
        
        return "\n".join(imports + test_methods + ["}", ""])

    def _call_api(self, prompt: str) -> dict:
        """
        Call the OpenAI API with enhanced error handling and retry logic.
        
        Args:
            prompt (str): The prompt to send to the API
            
        Returns:
            dict: API response
        """
        max_retries = 3
        retry_delay = 1  # seconds
        
        system_message = """You are a test generation assistant that writes JUnit 5 test methods.
IMPORTANT RULES:
1. Generate EXACTLY ONE test method
2. Start with @Test annotation
3. End with closing brace
4. Include required tags [MR1], [M1], [M2]
5. Use proper assertions and mocks
6. DO NOT write imports or explanations
7. DO NOT write multiple test methods
8. DO NOT write any text before or after the test method"""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=30
                )
                
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    # Convert OpenAI response to a format compatible with our existing code
                    return {
                        "generated_text": response.choices[0].message.content,
                        "request_id": response.id
                    }
                    
                self._log_error('api', "API returned an unexpected response format")
                
            except openai.APITimeoutError:
                self._log_error('api', f"API request timed out (attempt {attempt + 1})")
            except openai.APIError as e:
                self._log_error('api', f"API request failed: {str(e)}")
            except Exception as e:
                self._log_error('api', f"Unexpected error: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                
        return None

    def generate_summary_report(self) -> Dict:
        """
        Generate a comprehensive summary report of test generation metrics.
        
        Returns:
            Dict: Summary report containing various metrics
        """
        total_attempts = self.error_stats['generation_attempts']
        successful = self.error_stats['successful_generations']
        
        # Calculate success rates
        success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0
        
        # Calculate error distributions
        error_distribution = {
            'api_errors': len(self.error_stats['api_errors']),
            'extraction_errors': len(self.error_stats['extraction_errors']),
            'validation_errors': len(self.error_stats['validation_errors'])
        }
        
        # Analyze prompt performance
        prompt_performance = {}
        for complexity, stats in self.feedback_data['prompt_success_rate'].items():
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total'] * 100)
                prompt_performance[complexity] = {
                    'success_rate': success_rate,
                    'total_attempts': stats['total'],
                    'successful': stats['success']
                }
        
        # Generate report
        report = {
            'overall_metrics': {
                'total_attempts': total_attempts,
                'successful_generations': successful,
                'success_rate': success_rate,
                'average_attempts_per_success': (total_attempts / successful) if successful > 0 else 0
            },
            'error_distribution': error_distribution,
            'prompt_performance': prompt_performance,
            'complex_methods': list(self.feedback_data['complex_methods']),
            'common_error_patterns': list(self.feedback_data['error_patterns']),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Save report
        report_dir = "debug_output/reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, f"generation_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logging.info(f"Generation report saved to {report_file}")
            
        except Exception as e:
            logging.error(f"Failed to save generation report: {str(e)}")
        
        return report

    def print_summary_report(self, report: Dict = None):
        """
        Print a formatted summary report to the console.
        
        Args:
            report (Dict, optional): Report to print. If None, generates a new report.
        """
        if report is None:
            report = self.generate_summary_report()
            
        print("\n" + "="*80)
        print("Test Generation Summary Report")
        print("="*80)
        
        # Overall metrics
        print("\nOverall Metrics:")
        print(f"Total test generation attempts: {report['overall_metrics']['total_attempts']}")
        print(f"Successful generations: {report['overall_metrics']['successful_generations']}")
        print(f"Success rate: {report['overall_metrics']['success_rate']:.2f}%")
        print(f"Average attempts per success: {report['overall_metrics']['average_attempts_per_success']:.2f}")
        
        # Error distribution
        print("\nError Distribution:")
        for error_type, count in report['error_distribution'].items():
            print(f"{error_type}: {count}")
            
        # Prompt performance
        print("\nPrompt Performance by Complexity:")
        for complexity, stats in report['prompt_performance'].items():
            print(f"\n{complexity.title()} Methods:")
            print(f"Success rate: {stats['success_rate']:.2f}%")
            print(f"Total attempts: {stats['total_attempts']}")
            print(f"Successful: {stats['successful']}")
            
        # Complex methods
        if report['complex_methods']:
            print("\nComplex Methods Requiring Multiple Attempts:")
            for method in report['complex_methods']:
                print(f"- {method}")
                
        # Common error patterns
        if report['common_error_patterns']:
            print("\nCommon Error Patterns:")
            for pattern in report['common_error_patterns']:
                print(f"- {pattern}")
                
        print("\n" + "="*80)
        
    def test_connection(self) -> Optional[str]:
        """Test the API connection with a simple prompt."""
        try:
            test_prompt = """Generate a complete JUnit test for a calculator's add method.
The test must include actual implementation with assertions."""
            
            # Make the API call
            response = self._call_api(test_prompt)
            request_id = response.get('request_id', 'unknown')
            
            # Log the raw response for debugging
            logging.info(f"Test connection response (ID: {request_id}): {response}")
            
            if response:
                content = self._parse_api_response(response)
                if content:
                    # Extract and validate test code
                    test_code = self._extract_test_code(response)
                    if test_code:
                        logging.info(f"Test connection successful (ID: {request_id})")
                        logging.info(f"Generated valid test code:\n{test_code}")
                        return test_code
                    else:
                        logging.warning(f"Test connection returned content but failed to generate valid test code (ID: {request_id})")
                        return content
                else:
                    logging.warning(f"Test connection returned response but failed to extract content (ID: {request_id})")
            
            logging.error(f"Test connection failed to get valid response (ID: {request_id})")
            return None
            
        except Exception as e:
            logging.error(f"Test connection failed with error: {str(e)}")
            return None 