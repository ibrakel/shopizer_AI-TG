Refined Prompt for Composer Agent to Generate Maven Test Cases

Task Overview:

You are an AI Composer Agent integrated into a software project. Your task is to analyze all methods in the provided source code files and generate high-quality Maven-compatible test cases in Java. The test cases must align with the project requirements and metrics outlined below, ensuring adherence to Test-Driven Development (TDD) best practices. Additionally, include comments in each test method indicating the specific requirements ([MR], [SR], [CR]) and metrics ([M1], [M2], [M3], [M4], [M5]) being fulfilled.

Instructions:
	1.	Primary Objectives:
	    •	Generate Unit Tests:
	        •	For each method, create positive tests, negative tests, and edge case tests based on the method signature, implementation, and context ([MR1], [SR1]).
	    •	Generate End-to-End Tests:
	        •	Where applicable, create tests covering the interaction of multiple components ([MR2]).
	    •	Run Validation:
	        •	Simulate the execution of the generated tests against the codebase and log results ([MR3], [M4]).
	    •	Measure Coverage:
    	    •	Document the percentage of code covered by the generated tests ([MR4], [M1]).
	    •	Adhere to Standards:
	        •	Ensure all tests follow Java unit testing guidelines and naming conventions ([CR2], [M5]).
	2.	Metrics and Reporting:
	    •	Test Coverage ([M1]): Ensure generated tests achieve high coverage across methods, including edge cases and error scenarios.
	    •	Accuracy ([M2]): Validate that tests correctly evaluate method functionality.
	    •	Generation Time ([M3]): Track the time taken to generate test cases per method.
	    •	Pass Rate ([M4]): Measure the proportion of tests that execute successfully.
	    •	Standards Adherence ([M5]): Verify that tests follow Java conventions, including meaningful method names, proper use of assertions, and structured annotations.
	3.	Prompt Engineering Considerations:
	    •	Use method signatures, method bodies, and surrounding code context to understand functionality and generate comprehensive test cases ([SR1]).
	    •	Iteratively refine prompts for test generation to address errors and improve quality ([CR1]).
	4.	Structure of Tests:
	    •	Generate tests using JUnit 5 framework.
	    •	Follow Maven's directory structure:

src/
  ├── main/
  │    └── java/
  └── test/
       └── java/


	•	Use meaningful names for test classes and methods. For example:
	•	TestCalculateTax.java
	•	testCalculateTaxWithValidInput()
	•	testCalculateTaxWithZeroInput()
	•	testCalculateTaxWithInvalidRate()

	5.	Requirements in Test Cases:
	•	Comment on Each Test: Include comments specifying the requirements and metrics being fulfilled. For example:

@Test
void testCalculateTaxValidInput() {
    // [MR1, SR1] - Testing method functionality using valid inputs
    // [M1, M2] - Ensuring test coverage and accuracy
    double result = TaxCalculator.calculateTax(1000, 0.05);
    assertEquals(50, result, "Tax calculation failed for valid input");
}


	6.	Examples of Test Cases:
	•	Positive Test:

@Test
void testAddNumbersPositiveCase() {
    // [MR1, SR1] - Ensures basic functionality of addNumbers method
    // [M1, M2] - Verifies correct calculation and coverage
    int result = Calculator.addNumbers(3, 5);
    assertEquals(8, result, "Addition of 3 and 5 should return 8");
}


	•	Negative Test:

@Test
void testAddNumbersWithNull() {
    // [MR1, SR1] - Ensures error handling for null inputs
    // [M2, M5] - Validates input handling and adherence to standards
    assertThrows(NullPointerException.class, () -> {
        Calculator.addNumbers(null, 5);
    }, "Adding null value should throw NullPointerException");
}


	•	Edge Case Test:

@Test
void testAddNumbersBoundaryValues() {
    // [MR1, SR1] - Verifies handling of boundary values
    // [M1, M2] - Ensures edge cases are covered and accurate
    int result = Calculator.addNumbers(Integer.MAX_VALUE, 1);
    assertTrue(result < 0, "Addition should overflow and result in negative value");
}


	7.	Generate Reports:
	•	Detailed Report ([SR2]): Compare AI-generated test results against manually created tests, documenting:
	•	Test coverage percentage ([M1]).
	•	Success rate of tests ([M4]).
	•	Adherence to standards ([M5]).
	•	Average generation time per method ([M3]).
	•	Document errors or issues encountered during test generation and execution ([WR1]).
	8.	Validation and Output:
	•	Ensure all tests:
	•	Compile successfully within the Maven project.
	•	Pass when executed against the current codebase.
	•	Output test coverage and pass rates in a summarized format.

Final Output:

For each method:
	•	A suite of unit tests (positive, negative, and edge cases).
	•	Inline comments specifying the requirements ([MR], [SR], [CR]) and metrics ([M1], [M2], [M3], [M4], [M5]) addressed by the test.
	•	A detailed report comparing AI-generated test results to original test outcomes ([SR2]).

Begin analyzing the provided context and generate high-quality Maven-compatible test cases accordingly.






# Subsequent Prompts

1. **User Request**: Explore other classes, files, and methods that require test coverage beyond those already covered in the `TestContent` class.
   - **Assistant Action**: Proposed to search for public methods across the `sm-core-model` directory to identify additional methods that lack test coverage.

2. **User Request**: Focus on all identified classes and cover them with test cases.
   - **Assistant Action**: Outlined a plan to create test classes for each of the identified classes, including `GeoZone`, `CountryDescription`, `Currency`, `GeoZoneDescription`, `CustomerReviewDescription`, `Country`, `CustomerCriteria`, `CustomerList`, `CustomerOptionDescription`, and `CustomerOption`.

3. **User Request**: Resolve linter errors related to `CustomerService` and `Customer` in the `TestCustomerApi` class.
   - **Assistant Action**: Searched for the classes in the codebase to confirm their existence and location, then updated the import statements in the `TestCustomerApi` class.

4. **User Request**: Verify the available methods in `CustomerService` due to a linter error indicating that `getCustomerById` is not defined.
   - **Assistant Action**: Confirmed the absence of `getCustomerById` in `CustomerService` and suggested using `getByNick` instead.

5. **User Request**: Apply mock setups for `TestOrderApi` and `TestShoppingCartApi` classes.
   - **Assistant Action**: Updated the test classes with appropriate mock setups and resolved import issues.

6. **User Request**: Remove the unused import statement for `org.junit.jupiter.api.Assertions` in the `TestOrderApi` class.
   - **Assistant Action**: Removed the unused import statement to resolve the warning.

7. **User Request**: Write the subsequent prompts after the first one in the `Prompt.md` file.
   - **Assistant Action**: Added the subsequent prompts provided by the user after the initial one in the `Prompt.md` file.

- The user reported that tests did not show any coverage in JaCoCo and requested analysis of the test output and verification of runs.
- The assistant verified the presence of the `jacoco.exec` file and confirmed that execution data is being collected.
- The assistant opened the JaCoCo HTML report for the user to review coverage details and identify any issues with the coverage data.
