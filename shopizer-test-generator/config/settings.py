class Config:
    # List of source directories (relative to the project root)
    SOURCE_DIRS = [
        "sm-shop/src/main/java",
        "sm-shop-model/src/main/java",
        "sm-core-model/src/main/java",
        "sm-core/src/main/java",
        "sm-core-modules/src/main/java"
    ]
    # Base directory for generated test files
    TEST_OUTPUT_BASE = "sm-core/src/test/java"
    
    # Required test coverage threshold
    REQUIRED_COVERAGE = 0.90  # 90% coverage
    
    # Test types that will be generated for every method
    TEST_TYPES = ["POSITIVE", "NEGATIVE", "EDGE", "INTEGRATION", "ACCEPTANCE"]
    
    # Requirement tags for inline documentation in tests
    REQUIREMENT_TAGS = {
        "MR": "Main Requirement",
        "SR": "Secondary Requirement",
        "CR": "Coverage Requirement"
    }
    
    # Metric tags for inline documentation in tests
    METRIC_TAGS = {
        "M1": "Coverage",
        "M2": "Correctness",
        "M3": "Generation Time",
        "M4": "Pass Rate",
        "M5": "Standards Adherence"
    } 