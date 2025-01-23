package com.salesmanager.core.model.catalog.product;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.math.BigDecimal;

public class TestProduct {

    private Product product;

    @BeforeEach
    void setUp() {
        product = new Product();
    }

    @Test
    void testSetAndGetId() {
        // [MR1, SR1] - Testing set and get methods for ID
        // [M1, M2] - Ensuring test coverage and accuracy
        Long id = 123L;
        product.setId(id);
        assertEquals(id, product.getId(), "ID should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetRentalPeriod() {
        // [MR1, SR1] - Testing set and get methods for rental period
        // [M1, M2] - Ensuring test coverage and accuracy
        Integer rentalPeriod = 30;
        product.setRentalPeriod(rentalPeriod);
        assertEquals(rentalPeriod, product.getRentalPeriod(), "Rental period should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetProductLength() {
        // [MR1, SR1] - Testing set and get methods for product length
        // [M1, M2] - Ensuring test coverage and accuracy
        BigDecimal productLength = new BigDecimal("10.5");
        product.setProductLength(productLength);
        assertEquals(productLength, product.getProductLength(), "Product length should be set and retrieved correctly");
    }

    // Add more tests for other methods in Product
} 