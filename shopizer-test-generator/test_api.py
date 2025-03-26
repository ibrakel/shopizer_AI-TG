#!/usr/bin/env python3
"""
Simple script to test the API connection with DeepSeek model.
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

def save_debug_info(debug_dir: str, response: str, test_code: str = None):
    """Save debug information to files."""
    os.makedirs(debug_dir, exist_ok=True)
    
    # Save raw response
    with open(os.path.join(debug_dir, 'raw_response.json'), 'w') as f:
        try:
            # Try to format as JSON
            f.write(json.dumps(json.loads(response), indent=2))
        except:
            # If not JSON, write as plain text
            f.write(response)
            
    # Save extracted test code if available
    if test_code:
        with open(os.path.join(debug_dir, 'extracted_test.java'), 'w') as f:
            f.write(test_code)

def main():
    try:
        # Initialize the model
        logging.info("Initializing TestToCodeModel...")
        model = TestToCodeModel()
        
        # Test the connection
        logging.info("Testing API connection...")
        response = model.test_connection()
        
        if response:
            logging.info("API Response received:")
            print("-" * 80)
            print("Raw response:")
            print("-" * 80)
            print(response)
            print("-" * 80)
            
            # Save debug information
            debug_dir = "debug_output/latest_test"
            save_debug_info(debug_dir, str(response))
            logging.info(f"Debug information saved to {debug_dir}/")
            
            # Analyze response format
            logging.info("Response Analysis:")
            if isinstance(response, str):
                if "```java" in response:
                    logging.info("✓ Response contains Java code block markers")
                    start = response.find("```java")
                    end = response.find("```", start + 7)
                    if end > start:
                        code = response[start+7:end].strip()
                        logging.info("✓ Successfully extracted code block")
                        print("\nExtracted code:")
                        print("-" * 80)
                        print(code)
                        print("-" * 80)
                    else:
                        logging.warning("✗ Could not find end of code block")
                else:
                    logging.warning("✗ Response does not contain Java code block markers")
                
                if "@Test" in response:
                    logging.info("✓ Response contains @Test annotation")
                else:
                    logging.warning("✗ Response missing @Test annotation")
                    
                if "@DisplayName" in response:
                    logging.info("✓ Response contains @DisplayName annotation")
                else:
                    logging.warning("✗ Response missing @DisplayName annotation")
            else:
                logging.warning(f"✗ Unexpected response type: {type(response)}")
        else:
            logging.error("No response received from API")
            
    except Exception as e:
        logging.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    main() 