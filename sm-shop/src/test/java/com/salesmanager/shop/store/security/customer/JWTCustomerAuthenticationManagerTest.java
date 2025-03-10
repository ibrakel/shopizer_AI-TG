package com.salesmanager.shop.store.security.customer;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;

import com.salesmanager.shop.store.security.JWTTokenUtil;
import com.salesmanager.shop.store.security.common.CustomAuthenticationException;

public class JWTCustomerAuthenticationManagerTest {

    @InjectMocks
    private JWTCustomerAuthenticationManager jwtCustomerAuthenticationManager;

    @Mock
    private JWTTokenUtil jwtTokenUtil;

    @Mock
    private UserDetailsService jwtCustomerDetailsService;

    @Mock
    private HttpServletRequest request;

    @Mock
    private HttpServletResponse response;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testAttemptAuthenticationWithValidToken() throws Exception {
        // [MR1, SR1] - Valid token
        // [M1, M2] - Coverage + correctness
        when(request.getHeader("Authorization")).thenReturn("Bearer validToken");
        when(jwtTokenUtil.getUsernameFromToken("validToken")).thenReturn("validUser");
        UserDetails userDetails = mock(UserDetails.class);
        when(jwtCustomerDetailsService.loadUserByUsername("validUser")).thenReturn(userDetails);
        when(jwtTokenUtil.validateToken("validToken", userDetails)).thenReturn(true);

        Authentication authentication = jwtCustomerAuthenticationManager.attemptAuthentication(request, response);
        assertNotNull(authentication);
    }

    @Test
    void testAttemptAuthenticationWithInvalidToken() {
        // [MR1, SR1] - Invalid token
        // [M2, M5] - Error handling
        when(request.getHeader("Authorization")).thenReturn("Bearer invalidToken");
        when(jwtTokenUtil.getUsernameFromToken("invalidToken")).thenThrow(new IllegalArgumentException("Invalid token"));

        assertThrows(CustomAuthenticationException.class, () -> {
            jwtCustomerAuthenticationManager.attemptAuthentication(request, response);
        });
    }

    @Test
    void testAttemptAuthenticationWithNoToken() {
        // [MR1, SR1] - No token
        // [M2, M5] - Error handling
        when(request.getHeader("Authorization")).thenReturn(null);

        assertThrows(CustomAuthenticationException.class, () -> {
            jwtCustomerAuthenticationManager.attemptAuthentication(request, response);
        });
    }
} 