#!/usr/bin/env python3
"""
Test script for the enhanced test generator with OpenAI API integration.
"""

import logging
import json
import os
from src.models.test_to_code_model import TestToCodeModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Sample Java method for testing
SAMPLE_METHOD = """
    public int calculateTotal(List<OrderItem> items, double discount, boolean applyTax) {
        if (items == null || items.isEmpty()) {
            throw new IllegalArgumentException("Items list cannot be null or empty");
        }
        
        double total = 0;
        for (OrderItem item : items) {
            total += item.getPrice() * item.getQuantity();
        }
        
        if (discount > 0) {
            total = total * (1 - discount);
        }
        
        if (applyTax) {
            total = total * 1.2; // 20% tax
        }
        
        return (int) Math.round(total);
    }
"""

def test_prompt_generation():
    """Test dynamic prompt generation based on method complexity."""
    model = TestToCodeModel()
    
    # Extract method info
    method_info = model._extract_method_info(SAMPLE_METHOD)
    
    # Test prompt generation for different test types
    for test_type in ["Positive", "Negative", "Edge"]:
        prompt = model._create_prompt(method_info, test_type)
        
        logging.info(f"\nGenerated prompt for {test_type} test:")
        print("-" * 80)
        print(prompt)
        print("-" * 80)
        
        # Verify prompt contains key elements
        assert "calculateTotal" in prompt, "Method name missing from prompt"
        assert test_type in prompt, "Test type missing from prompt"
        assert "List<OrderItem>" in prompt, "Parameter type missing from prompt"
        
        logging.info(f"✓ {test_type} prompt validation passed")

def test_code_generation():
    """Test the complete test generation pipeline."""
    model = TestToCodeModel()
    
    # Extract method info
    method_info = model._extract_method_info(SAMPLE_METHOD)
    
    logging.info("\nTesting complete test generation pipeline...")
    
    # Generate test cases
    test_cases = []
    for test_type in ["Positive", "Negative", "Edge"]:
        logging.info(f"\nGenerating {test_type} test case...")
        
        # Create prompt
        prompt = model._create_prompt(method_info, test_type)
        logging.info("\nSending prompt to API:")
        print("-" * 80)
        print(prompt)
        print("-" * 80)
        
        # Call API and get response
        response = model._call_api(prompt)
        
        logging.info("\nRaw API Response:")
        print("-" * 80)
        print(json.dumps(response, indent=2) if response else "No response")
        print("-" * 80)
        
        if response:
            # Parse response
            content = model._parse_api_response(response)
            logging.info("\nExtracted content from response:")
            print("-" * 80)
            print(content if content else "No content extracted")
            print("-" * 80)
            
            # Try to extract test code
            test_code = model._extract_test_code(response)
            if test_code:
                test_cases.append(test_code)
                logging.info("✓ Test case generated successfully:")
                print("-" * 80)
                print(test_code)
                print("-" * 80)
            else:
                logging.error("✗ Failed to extract test code")
        else:
            logging.error("✗ No response from API")
    
    # Verify test generation metrics
    report = model.generate_summary_report()
    model.print_summary_report(report)
    
    return len(test_cases) > 0

def test_error_handling():
    """Test error handling and recovery mechanisms."""
    model = TestToCodeModel()
    
    # Test with invalid method
    invalid_method = "public void broken() {"
    
    logging.info("\nTesting error handling with invalid method...")
    method_info = model._extract_method_info(invalid_method)
    
    # Should handle gracefully and use template
    test_code = model.generate_test_case(method_info, "Positive")
    
    if test_code:
        logging.info("✓ Generated fallback template for invalid method")
        print("-" * 80)
        print(test_code)
        print("-" * 80)
    else:
        logging.warning("✗ Failed to generate fallback template")

def main():
    """Run all tests."""
    try:
        # Create output directories
        os.makedirs("debug_output/errors", exist_ok=True)
        os.makedirs("debug_output/feedback", exist_ok=True)
        os.makedirs("debug_output/reports", exist_ok=True)
        
        # Run tests
        logging.info("Starting test suite...")
        
        logging.info("\n1. Testing prompt generation...")
        test_prompt_generation()
        
        logging.info("\n2. Testing code generation...")
        success = test_code_generation()
        
        logging.info("\n3. Testing error handling...")
        test_error_handling()
        
        if success:
            logging.info("\n✓ All tests completed successfully")
        else:
            logging.error("\n✗ Some tests failed")
            
    except Exception as e:
        logging.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    main() 