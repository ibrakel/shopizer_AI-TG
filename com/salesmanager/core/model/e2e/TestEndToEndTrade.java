import java.util.Date;
import java.math.BigDecimal;
import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class TestEndToEndTrade {

    @Test
    public void testEndToEndTradeScenario() {
        // Product setup
        Product product = new Product();
        product.setProductLength(new BigDecimal("10.0"));
        product.setProductWidth(new BigDecimal("5.0"));
        product.setProductHeight(new BigDecimal("2.0"));
        product.setProductWeight(new BigDecimal("1.0"));

        // Customer setup
        Customer customer = new Customer();
        customer.setNick("john_doe");
        customer.setEmailAddress("john.doe@example.com");

        // Order setup
        Order order = new Order();
        order.setCustomerId(customer.getId());
        order.setStatus(OrderStatus.ORDERED);
        order.setDatePurchased(new Date());

        // CustomerReview setup
        CustomerReview review = new CustomerReview();
        review.setReviewRating(4.5);
        review.setReviewDate(new Date());
        review.setStatus(1);

        // Assertions
        assertEquals("john_doe", customer.getNick());
        assertEquals(OrderStatus.ORDERED, order.getStatus());
        assertEquals(4.5, review.getReviewRating(), 0.0);
    }
} 