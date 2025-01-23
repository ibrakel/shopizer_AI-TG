package com.salesmanager.core.utils;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Date;

public class TestCloneUtils {

    @Test
    void testCloneDate() {
        // [MR1, SR1] - Testing clone method for Date
        // [M1, M2] - Ensuring test coverage and accuracy
        Date originalDate = new Date();
        Date clonedDate = CloneUtils.clone(originalDate);
        assertNotNull(clonedDate, "Cloned date should not be null");
        assertEquals(originalDate, clonedDate, "Cloned date should be equal to the original date");
        assertNotSame(originalDate, clonedDate, "Cloned date should not be the same instance as the original date");
    }

    // Add more tests for other methods in CloneUtils
} 