"""
Templates for generating different types of JUnit 5 test methods.
These templates are used by the test generator to create standardized test cases.
"""

from config.settings import Config


def get_junit_import_block():
    """
    Returns a standardized import block for JUnit 5 test classes.
    
    Returns:
        str: Common JUnit 5 import statements
    """
    return """
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import static org.junit.jupiter.api.Assertions.*;
import org.mockito.Mock;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;
"""


def get_test_class_template(class_name):
    """
    Returns a template for a JUnit 5 test class.
    
    Args:
        class_name (str): Name of the class being tested
        
    Returns:
        str: Template for a JUnit 5 test class for the given class
    """
    return f"""
{get_junit_import_block()}

/**
 * Test class for {class_name}
 * Generated using standardized test generation template
 * 
 * Template structure:
 * 1. Setup and initialization
 * 2. Method-specific test groups:
 *    - Positive tests (valid inputs, expected behavior)
 *    - Negative tests (invalid inputs, error handling)
 *    - Edge tests (boundary conditions)
 *    - Integration tests (if applicable)
 * 3. Documentation and requirement mapping
 * 
 * [MR1, SR1] - Testing {class_name} functionality
 * [M1] - Method coverage
 * [M2] - Assertion coverage
 * [M3] - Edge case coverage
 * [M4] - Boundary testing
 * [M5] - Error handling and standards compliance
 */
public class Test{class_name} {{
    
    @InjectMocks
    private {class_name} instance;
    
    @BeforeEach
    public void setUp() {{
        MockitoAnnotations.openMocks(this);
        // Additional setup code will be added here
    }}
    
    @AfterEach
    public void tearDown() {{
        // Clean up resources if needed
    }}
    
    // Test methods will be added here
}}
"""


def get_positive_test_template(method_name, parameters, return_type):
    """
    Returns a template for a positive test method.
    
    Args:
        method_name (str): Name of the method being tested
        parameters (list): List of parameter type-name tuples
        return_type (str): Return type of the method
        
    Returns:
        str: Template for a positive test method
    """
    return f"""
    /**
     * POSITIVE test for method {method_name}
     * [MR1, SR1] - Testing {method_name} with valid inputs
     * [M1, M2] - Coverage and correctness
     * 
     * Note: For repository operations, always use saveAndFlush() instead of save()
     * Example: when(repository.saveAndFlush(any())).thenReturn(entity);
     */
    @Test
    @DisplayName("Test {method_name} with valid input")
    public void test{method_name.capitalize()}Positive() {{
        // 1. Setup test data
        // Example repository mock:
        // when(repository.saveAndFlush(any())).thenReturn(entity);
        
        // 2. Execute method
        // TODO: Call the method with valid inputs
        
        // 3. Verify results
        // Example repository verification:
        // verify(repository).saveAndFlush(entity);
    }}
"""


def get_negative_test_template(method_name, parameters, return_type):
    """
    Returns a template for a negative test method.
    
    Args:
        method_name (str): Name of the method being tested
        parameters (list): List of parameter type-name tuples
        return_type (str): Return type of the method
        
    Returns:
        str: Template for a negative test method
    """
    return f"""
    /**
     * NEGATIVE test for method {method_name}
     * [MR1] - Testing error conditions
     * [M2, M5] - Error handling
     */
    @Test
    @DisplayName("Test {method_name} with invalid input")
    public void test{method_name.capitalize()}Negative() {{
        // 1. Setup invalid test data
        // TODO: Set up invalid test data
        
        // 2. Execute method and verify error handling
        assertThrows(Exception.class, () -> {{
            // TODO: Call the method with invalid inputs
        }});
        
        // 3. Verify error handling
        // TODO: Verify error handling behavior
    }}
"""


def get_edge_test_template(method_name, parameters, return_type):
    """
    Returns a template for an edge case test method.
    
    Args:
        method_name (str): Name of the method being tested
        parameters (list): List of parameter type-name tuples
        return_type (str): Return type of the method
        
    Returns:
        str: Template for an edge case test method
    """
    return f"""
    /**
     * EDGE test for method {method_name}
     * [MR1] - Testing boundary conditions
     * [M3, M4] - Edge cases and boundaries
     */
    @Test
    @DisplayName("Test {method_name} with boundary values")
    public void test{method_name.capitalize()}Edge() {{
        // 1. Setup boundary conditions
        // TODO: Set up boundary test data
        
        // 2. Execute method with boundary values
        // TODO: Call the method with boundary values
        
        // 3. Verify boundary handling
        // TODO: Verify the expected outcome for boundary conditions
    }}
"""


def get_integration_test_template(method_name, parameters, return_type, dependencies):
    """
    Returns a template for an integration test method.
    
    Args:
        method_name (str): Name of the method being tested
        parameters (list): List of parameter type-name tuples
        return_type (str): Return type of the method
        dependencies (list): List of dependencies used by the method
        
    Returns:
        str: Template for an integration test method
    """
    return f"""
    /**
     * INTEGRATION test for method {method_name}
     * [CR1] - Testing integration with dependencies
     * [M1, M2] - Coverage and correctness
     */
    @Test
    @DisplayName("Integration test for {method_name}")
    public void test{method_name.capitalize()}Integration() {{
        // 1. Setup test data and mocks
        // TODO: Set up test data and configure mocks for dependencies
        
        // 2. Execute integrated workflow
        // TODO: Call the method that interacts with dependencies
        
        // 3. Verify interactions
        // TODO: Verify the expected outcome and interactions
    }}
"""


def get_acceptance_test_template(method_name, use_case_description):
    """
    Returns a template for an acceptance test method.
    
    Args:
        method_name (str): Name of the method being tested
        use_case_description (str): Description of the use case being tested
        
    Returns:
        str: Template for an acceptance test method
    """
    return f"""
    /**
     * ACCEPTANCE test for method {method_name}
     * [CR2] - Testing end-to-end scenario: {use_case_description}
     * [M1, M2] - Coverage and correctness
     */
    @Test
    @DisplayName("Acceptance test: {use_case_description}")
    public void test{method_name.capitalize()}Acceptance() {{
        // 1. Setup scenario
        // TODO: Set up test data for the full scenario
        
        // 2. Execute workflow
        // TODO: Execute the full scenario/workflow
        
        // 3. Verify end-to-end outcome
        // TODO: Verify the expected end-to-end outcome
    }}
"""


class TestTemplates:
    def format_test_class(self, package: str, class_name: str, imports: str, setup: str, test_methods: str, timestamp: str) -> str:
        """
        Format the full test class using the provided parameters.
        """
        template = f"""package {package};

{imports}

/**
 * Test class for {class_name.replace("Test", "")}
 * Generated using standardized test generation template
 * Generated on {timestamp}
 * 
 * Template structure:
 * 1. Setup and initialization
 * 2. Method-specific test groups:
 *    - Positive tests (valid inputs, expected behavior)
 *    - Negative tests (invalid inputs, error handling)
 *    - Edge tests (boundary conditions)
 *    - Integration tests (if applicable)
 * 3. Documentation and requirement mapping
 * 
 * [MR1, SR1] - Testing {class_name.replace("Test", "")} functionality
 * [M1] - Method coverage
 * [M2] - Assertion coverage
 * [M3] - Edge case coverage
 * [M4] - Boundary testing
 * [M5] - Error handling and standards compliance
 */
public class {class_name} {{
    private {class_name.replace("Test", "")} instance;

    {setup}

{test_methods}
}}
"""
        return template
    
    def format_test_method(self, method_name: str, description: str, requirements: str, metrics: str, method_body: str) -> str:
        """
        Format an individual test method.
        """
        template = f"""
    /**
     * {description}
     * {requirements}
     * {metrics}
     */
    @Test
    @DisplayName("{description}")
    public void {method_name}() {{
        // 1. Setup
        {method_body}
        
        // 2. Execute
        
        // 3. Verify
    }}
"""
        return template 