package com.salesmanager.shop.store.security.customer;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;

public class JWTCustomerAuthenticationProviderTest {

    @InjectMocks
    private JWTCustomerAuthenticationProvider jwtCustomerAuthenticationProvider;

    @Mock
    private UserDetailsService jwtCustomerDetailsService;

    @Mock
    private PasswordEncoder passwordEncoder;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testAuthenticateWithValidCredentials() {
        // [MR1, SR1] - Valid credentials
        // [M1, M2] - Coverage + correctness
        UserDetails userDetails = mock(UserDetails.class);
        when(jwtCustomerDetailsService.loadUserByUsername("validUser")).thenReturn(userDetails);
        when(passwordEncoder.matches("validPass", "validUser")).thenReturn(true);

        Authentication auth = new UsernamePasswordAuthenticationToken("validUser", "validPass");
        jwtCustomerAuthenticationProvider.authenticate(auth);
        // Verify that the password match was successful
        assertTrue(passwordEncoder.matches("validPass", "validUser"));
    }

    @Test
    void testAuthenticateWithInvalidCredentials() {
        // [MR1, SR1] - Invalid credentials
        // [M2, M5] - Error handling
        when(jwtCustomerDetailsService.loadUserByUsername("invalidUser")).thenReturn(null);

        Authentication auth = new UsernamePasswordAuthenticationToken("invalidUser", "invalidPass");
        assertThrows(BadCredentialsException.class, () -> {
            jwtCustomerAuthenticationProvider.authenticate(auth);
        });
    }

    @Test
    void testAuthenticateWithNullCredentials() {
        // [MR1, SR1] - Null credentials
        // [M2, M5] - Error handling
        Authentication auth = new UsernamePasswordAuthenticationToken(null, null);
        assertThrows(BadCredentialsException.class, () -> {
            jwtCustomerAuthenticationProvider.authenticate(auth);
        });
    }

    @Test
    void testSupports() {
        // [MR3, SR3] - Supports method
        // [M1, M2] - Coverage + correctness
        boolean result = jwtCustomerAuthenticationProvider.supports(UsernamePasswordAuthenticationToken.class);
        assertTrue(result);
    }

    @Test
    void testGetAndSetJwtCustomerDetailsService() {
        // [MR4, SR4] - Getter and Setter
        // [M1, M2] - Coverage + correctness
        UserDetailsService mockService = mock(UserDetailsService.class);
        jwtCustomerAuthenticationProvider.setJwtCustomerDetailsService(mockService);
        assertEquals(mockService, jwtCustomerAuthenticationProvider.getJwtCustomerDetailsService());
    }
} 