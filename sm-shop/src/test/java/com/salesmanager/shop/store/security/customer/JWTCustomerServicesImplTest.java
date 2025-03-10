package com.salesmanager.shop.store.security.customer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.mock;

import java.util.ArrayList;
import java.util.Collection;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.security.core.GrantedAuthority;

import com.salesmanager.core.model.customer.Customer;
import com.salesmanager.shop.store.security.user.JWTUser;

public class JWTCustomerServicesImplTest {

    @InjectMocks
    private JWTCustomerServicesImpl jwtCustomerServicesImpl;

    @Mock
    private Customer customer;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testUserDetails() {
        // [MR1, SR1] - Constructing JWTUser
        // [M1, M2] - Coverage + correctness
        Collection<GrantedAuthority> authorities = new ArrayList<>();
        JWTUser jwtUser = (JWTUser) jwtCustomerServicesImpl.userDetails("testUser", customer, authorities);

        assertNotNull(jwtUser);
        assertEquals("testUser", jwtUser.getUsername());
    }
} 