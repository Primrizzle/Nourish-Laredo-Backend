from django.test import TestCase, Client
from django.urls import reverse
import json

class WebhookTests(TestCase):
    def test_recurring_payment_webhook(self):
        client = Client()
        # Mocking the JSON payload Stripe sends for a subscription payment
        fake_payload = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "customer_email": "test@example.com",
                    "customer_name": "Test User",
                    "amount_paid": 2500,
                    "id": "in_test_123",
                    "subscription": "sub_test_123"
                }
            }
        }
        
        response = client.post(
            reverse('stripe_webhook'), 
            data=json.dumps(fake_payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="mock_signature" # You'll need to bypass signature check for local unit tests
        )
        
        self.assertEqual(response.status_code, 200)
        # Check if the donation was actually created in your test database
        from core.models import Donation
        self.assertTrue(Donation.objects.filter(processor_reference_id="in_test_123").exists())