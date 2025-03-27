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
        Create a prompt for generating a test case.
        
        Args:
            method_info (Dict): Method information dictionary
            test_type (str): Type of test to generate (Positive, Negative, Edge)
            
        Returns:
            str: Generated prompt
        """
        # Extract method information
        method_name = method_info.get('name', '')
        class_name = method_info.get('class_name', '')
        return_type = method_info.get('return_type', 'void')
        parameters = method_info.get('parameters', [])
        
        # Create a prompt for the API
        prompt = f"""
Generate a JUnit 5 test method for the Java method '{method_name}' in class '{class_name}'.
This should be a {test_type.lower()} test case.

Method signature:
```java
public {return_type} {method_name}({', '.join(parameters)})
```

Important Java syntax rules:
1. DO NOT create nested test methods or classes
2. Every statement must end with a semicolon
3. Use void for test method return type
4. Include ONLY the body of a single test method, not the entire class

Format your test method like this:
```java
@Test
void test{method_name}{test_type}() {{
    // [MR1] Test description
    // [M1, M2] Test metrics
    
    // Arrange
    // setup code here
    
    // Act
    // method call here
    
    // Assert
    // assertions here
}}
```

IMPORTANT: 
- Make the test method name include both the method name and the test type (test{method_name}{test_type})
- For Positive tests: Test normal operation with valid inputs
- For Negative tests: Test error handling with invalid inputs
- For Edge tests: Test boundary conditions and edge cases
- Use Mockito for mocking dependencies
- Include meaningful assertions
- Make sure all lines end with semicolons
"""
        return prompt

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
        """Extract code block from text.
        
        Args:
            content (str): Text to extract code from
            
        Returns:
            str: Extracted code or None if not found
        """
        if not content:
            return None
            
        try:
            # If the content already looks like a code block (no markdown)
            if content.strip().startswith('@Test') and 'void test' in content:
                logging.debug("Content already looks like a test method without markdown")
                return content.strip()
            
            # Look for code block with language identifier
            code_pattern = r"```(?:java)?\s*(.*?)```"
            match = re.search(code_pattern, content, re.DOTALL)
            if match:
                code = match.group(1).strip()
                logging.debug(f"Found code block with markdown: {code[:50]}...")
                return code
                
            # Look for a method with @Test annotation
            test_method_pattern = r"(@Test[\s\S]*?void\s+test\w+\s*\([\s\S]*?})"
            match = re.search(test_method_pattern, content, re.DOTALL)
            if match:
                code = match.group(1).strip()
                logging.debug(f"Found @Test method without markdown: {code[:50]}...")
                return code
                
            # Check if content seems to be just a code block by looking at key patterns
            if '@Test' in content and 'void test' in content and '{' in content and '}' in content:
                logging.debug("Content appears to be code but not in markdown format")
                return content.strip()
            
            # Keep the original content if it's short and likely just a code block
            if len(content) < 2000 and not content.startswith(('I am', 'Here', 'To test')):
                logging.debug("Using original content as last resort")
                return content.strip()
                
            return None
            
        except Exception as e:
            logging.error(f"Error extracting code block: {str(e)}")
            logging.debug(f"Problematic content start:\n{content[:200]}")
            return None

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

            # Extract code block from the content
            test_code = self._extract_code_block(content)
            
            if not test_code:
                logging.warning(f"No test code found in content (ID: {response_json.get('request_id', 'unknown')})")
                return None
                
            # Clean and validate the test code
            test_code = self._clean_generated_code(test_code)
            
            # Save the raw extracted test code
            debug_dir = "debug_output"
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            request_id = response_json.get('request_id', 'unknown')
            debug_file = os.path.join(debug_dir, f"test_code_{timestamp}_{request_id}.txt")
            
            with open(debug_file, "w", encoding='utf-8') as f:
                f.write(f"=== Extracted Test Code (ID: {request_id}) ===\n")
                f.write(test_code)
                f.write("\n")
            
            # Only validate if we want strict validation
            if self._is_valid_test_code(test_code):
                return test_code
            else:
                # Even if validation fails, if code has @Test, return it
                if '@Test' in test_code and 'void test' in test_code:
                    logging.warning(f"Returning test code despite validation failure (ID: {request_id})")
                    return test_code
                return None
            
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
            (r"void\s+test\w+\s*\(", "Invalid test method signature")
            # Removed assertion requirement as it's too strict
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
                r"\{\s*\}"  # Empty block
                # Removed more restrictive patterns
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
        Generate a test case for a given method.
        
        Args:
            method_info (Dict): Method information dictionary
            test_type (str): Type of test to generate (Positive, Negative, Edge)
            
        Returns:
            Optional[str]: Generated test code or None if generation failed
        """
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            try:
                # Create prompt with enhanced context
                prompt = self._create_enhanced_prompt(method_info, test_type)
                
                # Call API with retry logic
                response = self._call_api_with_retry(prompt)
                if not response:
                    self._log_error('api_error', 'No response from API', method_info.get('name'))
                    attempt += 1
                    continue
                
                # Extract and validate test code
                test_code = self._extract_test_code(response)
                if not test_code:
                    self._log_error('extraction_error', 'Failed to extract test code', method_info.get('name'))
                    attempt += 1
                    continue
                
                # Clean and validate the code
                test_code = self._clean_generated_code(test_code)
                if not self._is_valid_test_code(test_code):
                    self._log_error('validation_error', 'Invalid test code structure', method_info.get('name'))
                    attempt += 1
                    continue
                
                # Add required imports
                imports = self.get_required_imports(test_code)
                if imports:
                    test_code = self._add_imports(imports, test_code)
                
                # Update feedback data
                self._update_feedback_loop(method_info, True)
                
                return test_code
                
            except Exception as e:
                self._log_error('generation_error', str(e), method_info.get('name'))
                attempt += 1
        
        # If all attempts failed, generate a template test
        logging.warning(f"All attempts failed for {method_info.get('name')}, using template")
        return self._generate_template_test(method_info, test_type)

    def _create_enhanced_prompt(self, method_info: Dict, test_type: str) -> str:
        """
        Create an enhanced prompt with more context and guidance.
        
        Args:
            method_info (Dict): Method information
            test_type (str): Type of test
            
        Returns:
            str: Enhanced prompt
        """
        method_name = method_info.get('name', '')
        class_name = method_info.get('class_name', '')
        return_type = method_info.get('return_type', 'void')
        parameters = method_info.get('parameters', [])
        exceptions = method_info.get('throws', [])
        
        # Build comprehensive prompt
        prompt = f"""
Generate a high-quality JUnit 5 test method for the Java method '{method_name}' in class '{class_name}'.
This should be a {test_type.lower()} test case that follows Test-Driven Development best practices.

Method signature:
```java
public {return_type} {method_name}({', '.join(parameters)})
{' throws ' + ', '.join(exceptions) if exceptions else ''}
```

Requirements:
1. Test name must be 'test{method_name}{test_type}'
2. Include [MR], [SR], [CR] requirement tags in comments
3. Include [M1]-[M5] metric tags in comments
4. Use Mockito for mocking dependencies
5. Follow Arrange-Act-Assert pattern
6. Include meaningful assertions
7. Handle exceptions if method throws them
8. Use proper test data setup

Test structure:
```java
@Test
@DisplayName("{method_name} - {test_type} Test")
void test{method_name}{test_type}() {{
    // [MR1] Test description
    // [M1, M2] Test metrics
    
    // Arrange
    // Setup test data and mocks
    
    // Act
    // Call the method under test
    
    // Assert
    // Verify results and behavior
}}
```

Additional guidance:
- For Positive tests: Test normal operation with valid inputs
- For Negative tests: Test error handling with invalid inputs
- For Edge tests: Test boundary conditions and edge cases
- Mock external dependencies using Mockito
- Use assertThrows for exception testing
- Include verification of mock interactions
"""
        return prompt

    def _call_api_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Call the API with retry logic.
        
        Args:
            prompt (str): The prompt to send
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Optional[Dict]: API response or None if all attempts fail
        """
        attempt = 0
        while attempt < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a test generation expert. Generate high-quality, compilable JUnit 5 test cases."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    top_p=0.95,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
                
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    return response
                    
            except Exception as e:
                logging.error(f"API call attempt {attempt + 1} failed: {str(e)}")
                attempt += 1
                time.sleep(1)  # Add delay between retries
                
        return None

    def _add_imports(self, imports: List[str], test_code: str) -> str:
        """
        Add required imports to test code.
        
        Args:
            imports (List[str]): List of import statements
            test_code (str): Original test code
            
        Returns:
            str: Test code with imports added
        """
        # Common test-related imports
        standard_imports = [
            "org.junit.jupiter.api.Test",
            "org.junit.jupiter.api.DisplayName",
            "org.mockito.Mock",
            "org.mockito.InjectMocks",
            "org.mockito.junit.jupiter.MockitoExtension",
            "static org.junit.jupiter.api.Assertions.*",
            "static org.mockito.Mockito.*"
        ]
        
        # Combine standard imports with method-specific imports
        all_imports = list(set(standard_imports + imports))
        
        # Format import statements
        import_block = "\n".join(f"import {imp};" for imp in sorted(all_imports))
        
        return f"{import_block}\n\n{test_code}"

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
        """
        Generate a test class template.
        
        Args:
            package_name (str): Package name for the test class
            class_name (str): Name of the class being tested
            test_cases (List[str]): List of test case methods
            
        Returns:
            str: Complete test class template
        """
        # Clean up package name - remove ".test" if it was added
        if package_name.endswith(".test"):
            package_name = package_name[:-5]
            
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

    def _call_api(self, prompt):
        """
        Call OpenAI API to generate test code.
        
        Args:
            prompt (str): The prompt to send to the API
            
        Returns:
            dict: API response
        """
        try:
            system_message = """You are a Java testing expert specialized in generating JUnit 5 tests following Test-Driven Development best practices.

IMPORTANT FORMAT INSTRUCTIONS:
1. Generate ONLY the requested test method inside a Java code block.
2. NEVER include explanations, thoughts, or additional context.
3. ALWAYS include the @Test annotation.
4. ALWAYS use proper mocking for dependencies.
5. ALWAYS include meaningful assertions.
6. Format your response EXACTLY like this:

```java
@Test
void testMethodNameScenario() {
    // [MR1] Test description
    // [M1] Coverage metric
    
    // Test implementation with mocks and assertions
}
```

DO NOT include any text outside this code block. Return ONLY the test method."""

            # Make API call using OpenAI client
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Create a response object for compatibility with the rest of the code
            model_name = response.model if hasattr(response, 'model') else "gpt-3.5-turbo"
            response_id = response.id if hasattr(response, 'id') else f"id_{int(time.time())}"
            
            # Get the actual message content
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
            else:
                logging.warning("Unexpected API response format")
                content = ""
            
            # Store the response in a consistent format
            api_response = {
                'generated_text': content,
                'model': model_name,
                'request_id': response_id,
                'status_code': 200,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Save raw response for debugging
            debug_dir = "debug_output"
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = os.path.join(debug_dir, f"test_code_{timestamp}_{response_id}.txt")
            
            with open(debug_file, "w", encoding='utf-8') as f:
                f.write(content)
            
            return api_response
            
        except Exception as e:
            logging.error(f"API call failed: {str(e)}")
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