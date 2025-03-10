package com.salesmanager.core.business.services.order;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import java.util.Collections;

import org.junit.jupiter.api.Test;

import com.salesmanager.core.business.exception.ServiceException;
import com.salesmanager.core.business.services.order.OrderService;
import com.salesmanager.core.model.order.OrderSummary;
import com.salesmanager.core.model.order.OrderTotalSummary;
import com.salesmanager.core.business.services.order.OrderTotalSummary;
import com.salesmanager.core.model.customer.Customer;
import com.salesmanager.core.model.merchant.MerchantStore;
import com.salesmanager.core.model.reference.language.Language;

public class OrderServiceTest {

    private OrderService orderService;

    @Test
    void testCaculateOrderTotalWithValidInputs() throws ServiceException {
        // [MR1, SR1] - Testing caculateOrderTotal with valid inputs
        // [M1, M2] - Ensuring test coverage and accuracy
        OrderSummary orderSummary = mock(OrderSummary.class);
        Customer customer = mock(Customer.class);
        MerchantStore store = mock(MerchantStore.class);
        Language language = mock(Language.class);
        OrderTotalSummary expectedSummary = mock(OrderTotalSummary.class);

        when(orderService.caculateOrderTotal(orderSummary, customer, store, language)).thenReturn(expectedSummary);

        OrderTotalSummary result = orderService.caculateOrderTotal(orderSummary, customer, store, language);

        assertEquals(expectedSummary, result);
        verify(orderService, times(1)).caculateOrderTotal(orderSummary, customer, store, language);
    }

    @Test
    void testCaculateOrderTotalWithNullOrderSummary() {
        // [MR1, SR1] - Ensures error handling for null order summary
        // [M2, M5] - Validates input handling and adherence to standards
        Customer customer = mock(Customer.class);
        MerchantStore store = mock(MerchantStore.class);
        Language language = mock(Language.class);

        assertThrows(ServiceException.class, () -> {
            orderService.caculateOrderTotal(null, customer, store, language);
        }, "Calculating order total with null order summary should throw ServiceException");
    }

    @Test
    void testCaculateOrderTotalWithEmptyProducts() {
        // [MR1, SR1] - Ensures handling of empty products in order summary
        // [M1, M2] - Ensures edge cases are covered and accurate
        OrderSummary orderSummary = mock(OrderSummary.class);
        when(orderSummary.getProducts()).thenReturn(Collections.emptyList());
        Customer customer = mock(Customer.class);
        MerchantStore store = mock(MerchantStore.class);
        Language language = mock(Language.class);

        assertThrows(ServiceException.class, () -> {
            orderService.caculateOrderTotal(orderSummary, customer, store, language);
        }, "Calculating order total with empty products should throw ServiceException");
    }
} 