package com.salesmanager.core.business.services.customer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import com.salesmanager.core.business.exception.ServiceException;
import com.salesmanager.core.business.repositories.customer.CustomerRepository;
import com.salesmanager.core.model.common.Address;
import com.salesmanager.core.model.customer.Customer;
import com.salesmanager.core.model.customer.CustomerCriteria;
import com.salesmanager.core.model.customer.CustomerList;
import com.salesmanager.core.model.merchant.MerchantStore;
import com.salesmanager.core.modules.utils.GeoLocation;

public class CustomerServicesImplTest {

    @InjectMocks
    private CustomerServiceImpl customerServiceImpl;

    @Mock
    private CustomerRepository customerRepository;

    @Mock
    private MerchantStore store;

    @Mock
    private GeoLocation geoLocation;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testGetByName() {
        // [MR1, SR1] - Retrieve customers by name
        // [M1, M2] - Coverage + correctness
        List<Customer> customers = mock(List.class);
        when(customerRepository.findByName("John")).thenReturn(customers);

        List<Customer> result = customerServiceImpl.getByName("John");
        assertNotNull(result);
    }

    @Test
    void testGetById() {
        // [MR1, SR1] - Retrieve customer by ID
        // [M1, M2] - Coverage + correctness
        Customer customer = mock(Customer.class);
        when(customerRepository.findOne(1L)).thenReturn(customer);

        Customer result = customerServiceImpl.getById(1L);
        assertNotNull(result);
    }

    @Test
    void testGetByNick() {
        // [MR1, SR1] - Retrieve customer by nickname
        // [M1, M2] - Coverage + correctness
        Customer customer = mock(Customer.class);
        when(customerRepository.findByNick("nickname")).thenReturn(customer);

        Customer result = customerServiceImpl.getByNick("nickname");
        assertNotNull(result);
    }

    @Test
    void testGetListByStore() {
        // [MR1, SR1] - Retrieve customers by store
        // [M1, M2] - Coverage + correctness
        List<Customer> customers = mock(List.class);
        when(customerRepository.findByStore(store.getId())).thenReturn(customers);

        List<Customer> result = customerServiceImpl.getListByStore(store);
        assertNotNull(result);
    }

    @Test
    void testGetCustomerAddress() throws ServiceException {
        // [MR1, SR1] - Retrieve customer address by store and IP
        // [M1, M2] - Coverage + correctness
        Address address = mock(Address.class);
        when(geoLocation.getAddress("127.0.0.1")).thenReturn(address);

        Address result = customerServiceImpl.getCustomerAddress(store, "127.0.0.1");
        assertNotNull(result);
    }

    @Test
    void testSaveOrUpdate() throws ServiceException {
        // [MR1, SR1] - Save or update customer
        // [M1, M2] - Coverage + correctness
        Customer customer = mock(Customer.class);
        customerServiceImpl.saveOrUpdate(customer);
    }

    @Test
    void testDelete() throws ServiceException {
        // [MR1, SR1] - Delete customer
        // [M1, M2] - Coverage + correctness
        Customer customer = mock(Customer.class);
        when(customerRepository.findOne(1L)).thenReturn(customer);

        customerServiceImpl.delete(customer);
    }
} 