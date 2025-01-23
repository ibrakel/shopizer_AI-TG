package com.salesmanager.core.model.customer;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Date;
import java.util.List;
import java.util.ArrayList;

public class TestCustomer {

    private Customer customer;

    @BeforeEach
    void setUp() {
        customer = new Customer();
    }

    @Test
    void testSetAndGetId() {
        // [MR1, SR1] - Testing set and get methods for ID
        // [M1, M2] - Ensuring test coverage and accuracy
        Long id = 123L;
        customer.setId(id);
        assertEquals(id, customer.getId(), "ID should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetDateOfBirth() {
        // [MR1, SR1] - Testing set and get methods for date of birth
        // [M1, M2] - Ensuring test coverage and accuracy
        Date dateOfBirth = new Date();
        customer.setDateOfBirth(dateOfBirth);
        assertEquals(dateOfBirth, customer.getDateOfBirth(), "Date of birth should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetEmailAddress() {
        // [MR1, SR1] - Testing set and get methods for email address
        // [M1, M2] - Ensuring test coverage and accuracy
        String emailAddress = "test@example.com";
        customer.setEmailAddress(emailAddress);
        assertEquals(emailAddress, customer.getEmailAddress(), "Email address should be set and retrieved correctly");
    }

    // Add more tests for other methods in Customer
} 