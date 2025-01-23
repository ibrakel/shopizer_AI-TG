package com.salesmanager.core.model.common;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class TestAddress {

    private Address address;

    @BeforeEach
    void setUp() {
        address = new Address();
    }

    @Test
    void testSetAndGetPostalCode() {
        // [MR1, SR1] - Testing set and get methods for postal code
        // [M1, M2] - Ensuring test coverage and accuracy
        String postalCode = "12345";
        address.setPostalCode(postalCode);
        assertEquals(postalCode, address.getPostalCode(), "Postal code should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetStateProvince() {
        // [MR1, SR1] - Testing set and get methods for state province
        // [M1, M2] - Ensuring test coverage and accuracy
        String stateProvince = "Test State";
        address.setStateProvince(stateProvince);
        assertEquals(stateProvince, address.getStateProvince(), "State province should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetCountry() {
        // [MR1, SR1] - Testing set and get methods for country
        // [M1, M2] - Ensuring test coverage and accuracy
        String country = "Test Country";
        address.setCountry(country);
        assertEquals(country, address.getCountry(), "Country should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetZone() {
        // [MR1, SR1] - Testing set and get methods for zone
        // [M1, M2] - Ensuring test coverage and accuracy
        String zone = "Test Zone";
        address.setZone(zone);
        assertEquals(zone, address.getZone(), "Zone should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetCity() {
        // [MR1, SR1] - Testing set and get methods for city
        // [M1, M2] - Ensuring test coverage and accuracy
        String city = "Test City";
        address.setCity(city);
        assertEquals(city, address.getCity(), "City should be set and retrieved correctly");
    }

    // Add more tests for other methods in Address
} 