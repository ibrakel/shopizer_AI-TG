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
 */
public class Test{class_name} {{
    
    @InjectMocks
    private {class_name} instance;
    
    @BeforeEach
    public void setUp() {{
        MockitoAnnotations.openMocks(this);
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
    @Test
    @DisplayName("Test {method_name} with valid input")
    public void test{method_name.capitalize()}ValidInput() {{
        // [MR1, SR1] - Testing method with valid inputs
        // [M1, M2, M3, M4, M5] - Coverage, correctness, time, pass rate, standards
        
        // Arrange
        // TODO: Set up test data
        
        // Act
        // TODO: Call the method with valid inputs
        
        // Assert
        // TODO: Verify the expected outcome
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
    @Test
    @DisplayName("Test {method_name} with invalid input")
    public void test{method_name.capitalize()}InvalidInput() {{
        // [MR2, SR2] - Testing method with invalid inputs
        // [M1, M2, M3, M4, M5] - Coverage, correctness, time, pass rate, standards
        
        // Arrange
        // TODO: Set up invalid test data
        
        // Act & Assert
        assertThrows(Exception.class, () -> {{
            // TODO: Call the method with invalid inputs
        }});
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
    @Test
    @DisplayName("Test {method_name} with boundary values")
    public void test{method_name.capitalize()}BoundaryValues() {{
        // [MR3, SR3] - Testing method with boundary values
        // [M1, M2, M3, M4, M5] - Coverage, correctness, time, pass rate, standards
        
        // Arrange
        // TODO: Set up boundary test data
        
        // Act
        // TODO: Call the method with boundary values
        
        // Assert
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
    @Test
    @DisplayName("Integration test for {method_name}")
    public void test{method_name.capitalize()}Integration() {{
        // [CR1] - Testing integration with other components
        // [M1, M2, M3, M4, M5] - Coverage, correctness, time, pass rate, standards
        
        // Arrange
        // TODO: Set up test data and configure mocks for dependencies
        
        // Act
        // TODO: Call the method that interacts with dependencies
        
        // Assert
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
    @Test
    @DisplayName("Acceptance test: {use_case_description}")
    public void test{method_name.capitalize()}Acceptance() {{
        // [CR2] - Testing end-to-end scenario: {use_case_description}
        // [M1, M2, M3, M4, M5] - Coverage, correctness, time, pass rate, standards
        
        // Arrange
        // TODO: Set up test data for the full scenario
        
        // Act
        // TODO: Execute the full scenario/workflow
        
        // Assert
        // TODO: Verify the expected end-to-end outcome
    }}
"""


class TestTemplates:
    def format_test_class(self, package: str, class_name: str, imports: str, setup: str, test_methods: str, timestamp: str) -> str:
        """
        Format the full test class using the provided parameters.
        """
        template = f"""{imports}

/**
 * Test class for {class_name.replace("Test", "")}
 * Generated on {timestamp}
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
    public void {method_name}() {{
        {method_body}
    }}
"""
        return template 