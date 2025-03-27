package com.salesmanager.core.business.services.order;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import com.salesmanager.core.business.exception.ServiceException;
import com.salesmanager.core.business.repositories.order.OrderRepository;
import com.salesmanager.core.business.services.customer.CustomerService;
import com.salesmanager.core.model.customer.Customer;
import com.salesmanager.core.model.merchant.MerchantStore;
import com.salesmanager.core.model.order.Order;
import com.salesmanager.core.model.order.OrderCriteria;
import com.salesmanager.core.model.order.OrderList;
import com.salesmanager.core.model.order.OrderTotalSummary;
import com.salesmanager.core.model.order.orderproduct.OrderProduct;
import com.salesmanager.core.model.order.orderproduct.OrderProductDownload;
import com.salesmanager.core.model.order.orderstatus.OrderStatus;
import com.salesmanager.core.model.order.orderstatus.OrderStatusHistory;
import com.salesmanager.core.model.payments.Payment;
import com.salesmanager.core.model.payments.Transaction;
import com.salesmanager.core.model.shoppingcart.ShoppingCartItem;

@RunWith(MockitoJUnitRunner.class)
public class OrderServiceImplTest {

    @Mock
    private OrderRepository orderRepository;
    
    @Mock
    private CustomerService customerService;
    
    @InjectMocks
    private OrderServiceImpl orderService;
    
    private MerchantStore merchantStore;
    private Customer customer;
    private Order order;
    private OrderStatusHistory orderStatusHistory;
    
    @Before
    public void setUp() {
        merchantStore = new MerchantStore();
        merchantStore.setId(1);
        merchantStore.setStorename("Test Store");
        
        customer = new Customer();
        customer.setId(1L);
        customer.setMerchantStore(merchantStore);
        
        order = new Order();
        order.setId(1L);
        order.setCustomerId(1L);
        order.setMerchant(merchantStore);
        order.setOrderHistory(new HashSet<>());
        order.setOrderProducts(new HashSet<>());
        order.setStatus(OrderStatus.ORDERED);
        
        orderStatusHistory = new OrderStatusHistory();
        orderStatusHistory.setStatus(OrderStatus.PROCESSED);
        orderStatusHistory.setDateAdded(new Date());
        orderStatusHistory.setComments("Order has been processed");
    }
    
    /**
     * [MR1] - Tests adding order status history to an order
     * [M1] - Method coverage: addOrderStatusHistory
     * [M2] - Code correctness: verifies the history is added to the order's history set
     */
    @Test
    public void testAddOrderStatusHistory_ShouldAddHistoryToOrder() throws ServiceException {
        // Given
        when(orderRepository.saveAndFlush(any(Order.class))).thenReturn(order);
        
        // When
        orderService.addOrderStatusHistory(order, orderStatusHistory);
        
        // Then
        assertEquals(1, order.getOrderHistory().size());
        assertTrue(order.getOrderHistory().contains(orderStatusHistory));
        assertEquals(order, orderStatusHistory.getOrder());
        verify(orderRepository).saveAndFlush(order);
    }
    
    /**
     * [MR2] - Tests retrieving an order by id and store
     * [M1] - Method coverage: getOrder
     * [M3] - Input validation: verifies the method handles valid id and store
     */
    @Test
    public void testGetOrder_ShouldReturnOrderWhenExisting() {
        // Given
        when(orderRepository.findOne(anyLong(), anyInt())).thenReturn(order);
        
        // When
        Order result = orderService.getOrder(1L, merchantStore);
        
        // Then
        assertNotNull(result);
        assertEquals(order, result);
        verify(orderRepository).findOne(1L, merchantStore.getId());
    }
    
    /**
     * [CR1] - Tests checking if an order has download files
     * [M1] - Method coverage: hasDownloadFiles
     * [M5] - Edge cases: tests order with no download files
     */
    @Test
    public void testHasDownloadFiles_ShouldReturnFalseWhenNoDownloads() throws ServiceException {
        // Given
        Set<OrderProduct> products = new HashSet<>();
        OrderProduct product = new OrderProduct();
        product.setDownloads(new HashSet<>());
        products.add(product);
        order.setOrderProducts(products);
        
        // When
        boolean result = orderService.hasDownloadFiles(order);
        
        // Then
        assertFalse(result);
    }
    
    /**
     * [CR2] - Tests checking if an order has download files when it does have them
     * [M1] - Method coverage: hasDownloadFiles
     * [M5] - Edge cases: tests order with download files
     */
    @Test
    public void testHasDownloadFiles_ShouldReturnTrueWhenHasDownloads() throws ServiceException {
        // Given
        Set<OrderProduct> products = new HashSet<>();
        OrderProduct product = new OrderProduct();
        Set<OrderProductDownload> downloads = new HashSet<>();
        downloads.add(new OrderProductDownload());
        product.setDownloads(downloads);
        products.add(product);
        order.setOrderProducts(products);
        
        // When
        boolean result = orderService.hasDownloadFiles(order);
        
        // Then
        assertTrue(result);
    }
    
    /**
     * [SR1] - Tests saving a new order
     * [M1] - Method coverage: saveOrUpdate
     * [M2] - Code correctness: verifies the method correctly identifies a new order
     */
    @Test
    public void testSaveOrUpdate_ShouldCreateNewOrder() throws ServiceException {
        // Given
        Order newOrder = new Order();
        newOrder.setId(null); // New order with no ID
        when(orderRepository.saveAndFlush(any(Order.class))).thenReturn(newOrder);
        
        // When
        orderService.saveOrUpdate(newOrder);
        
        // Then
        verify(orderRepository).saveAndFlush(newOrder);
    }
    
    /**
     * [SR2] - Tests updating an existing order
     * [M1] - Method coverage: saveOrUpdate
     * [M2] - Code correctness: verifies the method correctly identifies an existing order
     */
    @Test
    public void testSaveOrUpdate_ShouldUpdateExistingOrder() throws ServiceException {
        // Given
        // order already has ID=1L set in setUp()
        when(orderRepository.saveAndFlush(any(Order.class))).thenReturn(order);
        
        // When
        orderService.saveOrUpdate(order);
        
        // Then
        verify(orderRepository).saveAndFlush(order);
    }
} 