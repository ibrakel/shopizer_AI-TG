package com.salesmanager.core.model.system;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.HashMap;
import java.util.Map;

public class TestMerchantConfig {

    private MerchantConfig merchantConfig;

    @BeforeEach
    void setUp() {
        merchantConfig = new MerchantConfig();
    }

    @Test
    void testSetAndGetDisplayCustomerSection() {
        // [MR1, SR1] - Testing set and get methods for displayCustomerSection
        // [M1, M2] - Ensuring test coverage and accuracy
        merchantConfig.setDisplayCustomerSection(true);
        assertTrue(merchantConfig.isDisplayCustomerSection(), "Display customer section should be true when set to true");
    }

    @Test
    void testSetAndGetDisplayContactUs() {
        // [MR1, SR1] - Testing set and get methods for displayContactUs
        // [M1, M2] - Ensuring test coverage and accuracy
        merchantConfig.setDisplayContactUs(true);
        assertTrue(merchantConfig.isDisplayContactUs(), "Display contact us should be true when set to true");
    }

    @Test
    void testSetAndGetUseDefaultSearchConfig() {
        // [MR1, SR1] - Testing set and get methods for useDefaultSearchConfig
        // [M1, M2] - Ensuring test coverage and accuracy
        Map<String, Boolean> searchConfig = new HashMap<>();
        searchConfig.put("en", true);
        merchantConfig.setUseDefaultSearchConfig(searchConfig);
        assertEquals(searchConfig, merchantConfig.getUseDefaultSearchConfig(), "Use default search config should be set and retrieved correctly");
    }

    // Add more tests for other methods in MerchantConfig
} 