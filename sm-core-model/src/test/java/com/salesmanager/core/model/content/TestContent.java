package com.salesmanager.core.model.content;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Date;
import java.util.List;
import java.util.ArrayList;

public class TestContent {

    private Content content;

    @BeforeEach
    void setUp() {
        content = new Content();
    }

    @Test
    void testSetAndGetId() {
        // [MR1, SR1] - Testing set and get methods for ID
        // [M1, M2] - Ensuring test coverage and accuracy
        Long id = 123L;
        content.setId(id);
        assertEquals(id, content.getId(), "ID should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetProductGroup() {
        // [MR1, SR1] - Testing set and get methods for product group
        // [M1, M2] - Ensuring test coverage and accuracy
        String productGroup = "Test Group";
        content.setProductGroup(productGroup);
        assertEquals(productGroup, content.getProductGroup(), "Product group should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetCode() {
        // [MR1, SR1] - Testing set and get methods for code
        // [M1, M2] - Ensuring test coverage and accuracy
        String code = "CODE123";
        content.setCode(code);
        assertEquals(code, content.getCode(), "Code should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetVisible() {
        // [MR1, SR1] - Testing set and get methods for visibility
        // [M1, M2] - Ensuring test coverage and accuracy
        content.setVisible(true);
        assertTrue(content.isVisible(), "Content should be visible when set to true");
        content.setVisible(false);
        assertFalse(content.isVisible(), "Content should not be visible when set to false");
    }

    @Test
    void testSetAndGetDescriptions() {
        // [MR1, SR1] - Testing set and get methods for descriptions
        // [M1, M2] - Ensuring test coverage and accuracy
        List<ContentDescription> descriptions = new ArrayList<>();
        content.setDescriptions(descriptions);
        assertEquals(descriptions, content.getDescriptions(), "Descriptions should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetContentType() {
        // [MR1, SR1] - Testing set and get methods for content type
        // [M1, M2] - Ensuring test coverage and accuracy
        ContentType contentType = ContentType.BOX; // Use correct enum value
        content.setContentType(contentType);
        assertEquals(contentType, content.getContentType(), "Content type should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetSortOrder() {
        // [MR1, SR1] - Testing set and get methods for sort order
        // [M1, M2] - Ensuring test coverage and accuracy
        Integer sortOrder = 1;
        content.setSortOrder(sortOrder);
        assertEquals(sortOrder, content.getSortOrder(), "Sort order should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetContentPosition() {
        // [MR1, SR1] - Testing set and get methods for content position
        // [M1, M2] - Ensuring test coverage and accuracy
        ContentPosition contentPosition = ContentPosition.LEFT; // Use correct enum value
        content.setContentPosition(contentPosition);
        assertEquals(contentPosition, content.getContentPosition(), "Content position should be set and retrieved correctly");
    }

    @Test
    void testSetAndGetLinkToMenu() {
        // [MR1, SR1] - Testing set and get methods for link to menu
        // [M1, M2] - Ensuring test coverage and accuracy
        content.setLinkToMenu(true);
        assertTrue(content.isLinkToMenu(), "Link to menu should be true when set to true");
        content.setLinkToMenu(false);
        assertFalse(content.isLinkToMenu(), "Link to menu should be false when set to false");
    }

    // Add more tests for other methods in Content
} 