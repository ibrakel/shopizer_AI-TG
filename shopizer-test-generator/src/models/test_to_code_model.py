"""
Test-to-code model implementation using remote DeepSeek model via API endpoint.
This module provides functionality to generate test cases from source code.
"""

import requests
from typing import List, Dict, Optional
import logging
import re
import os
import datetime
import json

class TestToCodeModel:
    """
    A model that generates test cases from source code using remote DeepSeek model.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the test-to-code model.
        
        Args:
            api_key (str, optional): Not used
        """
        # Use the provided ngrok URL
        self.api_url = "https://332d-34-125-194-162.ngrok-free.app/generate"
        try:
            # Test the connection
            response = requests.post(
                self.api_url, 
                headers={"Content-Type": "application/json"},
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a test generation assistant."
                        },
                        {
                            "role": "user",
                            "content": "test connection"
                        }
                    ]
                }
            )
            if response.status_code == 200:
                logging.info("Connected to remote DeepSeek model successfully")
            else:
                logging.warning(f"Connection test returned status code {response.status_code}")
        except Exception as e:
            logging.error(f"Failed to connect to remote DeepSeek model: {str(e)}")
            raise

    def _create_prompt(self, method_info: Dict, test_type: str) -> str:
        prompt = f"""Generate a JUnit 5 test case for the following method using this exact format:
1: @Test
2: @DisplayName("{method_info['name']} - {test_type} Test")
3: public void test{method_info['name']}{test_type}() {{
4:     // [MR1, SR1] Test Description
5:     // [M1, M2] Coverage and correctness metrics
6:     // Setup test data and mocks
7:     // Execute method under test
8:     // Verify results
9: }}

Rules:
1. Follow the exact line numbers and indentation shown above
2. Replace placeholders with actual test code
3. Keep the structure but fill in implementation details
4. Include proper assertions and mocking
5. Add relevant imports at the top
6. Handle exceptions appropriately
7. Document test coverage goals

Method Information:
Name: {method_info['name']}
Return Type: {method_info.get('return_type', 'void')}
Parameters: {method_info.get('parameters', [])}
Exceptions: {method_info.get('exceptions', [])}
Test Type: {test_type}

Generate the complete test method following this structure exactly."""
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
        """Extract code block from message content.
        
        Args:
            content (str): Message content containing code
            
        Returns:
            Optional[str]: Extracted code block if found, None otherwise
        """
        if not content:
            return None
        
        try:
            # Try to extract code between ```java and ``` markers
            code_pattern = r"```java\s*(.*?)\s*```"
            matches = re.findall(code_pattern, content, re.DOTALL)
            
            if matches:
                return matches[0].strip()
            
            # Fallback: Try to extract just the test method
            test_pattern = r"@Test.*?}\s*}"
            matches = re.findall(test_pattern, content, re.DOTALL)
            
            if matches:
                return matches[0].strip()
            
            logging.warning("No code block found in content")
            return None
            
        except Exception as e:
            logging.error(f"Error extracting code block: {str(e)}")
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
        """Check if the generated code is a valid test."""
        if not code:
            return False
        
        required_elements = [
            '@Test',
            '@DisplayName',
            'public void test',
            '{'
        ]
        
        return all(element in code for element in required_elements)

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
        """Generate a test case for a method."""
        max_attempts = 3
        attempt = 1
        success = False
        test_code = None
        
        while attempt <= max_attempts and not success:
            try:
                prompt = self._create_prompt(method_info, test_type)
                response = self._call_api(prompt)
                
                if response:
                    test_code = self._extract_test_code(response)
                    if test_code:
                        success = True
                    else:
                        logging.warning(f"Failed to extract test code (attempt {attempt})")
                else:
                    logging.warning(f"API call failed (attempt {attempt})")
                    
            except Exception as e:
                logging.error(f"Error generating {test_type} test (attempt {attempt}): {str(e)}")
                
            attempt += 1
            
        return test_code

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
        """Call the API to generate test code.
        
        Args:
            prompt (str): The prompt to send to the API
            
        Returns:
            dict: API response JSON
            
        Raises:
            Exception: If API call fails
        """
        url = "https://332d-34-125-194-162.ngrok-free.app/generate"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Format the request according to the API's expected structure
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": """You are a test generation assistant. Follow these rules:

1. Only respond with complete, implemented test code
2. Always wrap your response in <response></response> tags
3. Always include imports
4. Always use proper assertions
5. Never return templates or placeholders

Example response:
<response>
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

@Test
@DisplayName("add - Simple Test")
public void testAddSimple() {
    // Arrange
    Calculator calculator = new Calculator();
    int a = 5, b = 3;
    
    // Act
    int result = calculator.add(a, b);
    
    // Assert
    assertEquals(8, result);
}
```
</response>"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": False,
            "stop": ["</response>"],
            "echo": False
        }
        
        # Create debug directory if it doesn't exist
        debug_dir = "debug_output"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Create debug file with timestamp and request ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        request_id = os.urandom(8).hex()
        debug_file = os.path.join(debug_dir, f"api_debug_{timestamp}_{request_id}.txt")
        
        try:
            # Log request details
            with open(debug_file, "w", encoding='utf-8') as f:
                f.write(f"=== API Request (ID: {request_id}) ===\n")
                f.write(f"URL: {url}\n")
                f.write(f"Headers: {headers}\n")
                f.write(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}\n\n")
            
            # Make API call with increased timeout
            response = requests.post(url, headers=headers, json=data, timeout=120)  # Increased timeout
            
            # Log raw response immediately
            with open(debug_file, "a", encoding='utf-8') as f:
                f.write(f"=== Raw API Response (ID: {request_id}) ===\n")
                f.write(f"Status: {response.status_code}\n")
                f.write(f"Headers: {dict(response.headers)}\n")
                f.write(f"Body: {response.text}\n\n")
            
            # Check response status
            if response.status_code != 200:
                error_msg = f"API request {request_id} failed with status {response.status_code}: {response.text}"
                logging.error(error_msg)
                raise Exception(error_msg)
            
            # Parse response JSON
            try:
                response_json = response.json()
                
                # Validate response structure
                if not isinstance(response_json, dict):
                    raise ValueError(f"Expected dict response, got {type(response_json)}")
                
                # Log parsed response
                with open(debug_file, "a", encoding='utf-8') as f:
                    f.write(f"=== Parsed Response (ID: {request_id}) ===\n")
                    f.write(json.dumps(response_json, indent=2, ensure_ascii=False))
                    f.write("\n")
                
                # Add request ID to response for tracking
                response_json['request_id'] = request_id
                return response_json
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse API response as JSON (ID: {request_id}): {str(e)}\nResponse text: {response.text}"
                logging.error(error_msg)
                raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request {request_id} failed: {str(e)}"
            logging.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected error in API call {request_id}: {str(e)}"
            logging.error(error_msg)
            raise

    def test_connection(self) -> Optional[str]:
        """Test the API connection with a simple prompt."""
        try:
            test_prompt = """<instruction>
Generate a complete JUnit test for a calculator's add method.
The test must include actual implementation with assertions.
Wrap your response in <response></response> tags.
</instruction>"""
            
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