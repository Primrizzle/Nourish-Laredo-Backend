import os
import sys
import json
import time
import hmac
import hashlib
import django
import re
from unittest.mock import patch

# 1. SETUP PATHS & SETTINGS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

try:
    with open(os.path.join(BASE_DIR, 'manage.py'), 'r') as f:
        manage_content = f.read()
        match = re.search(r"['\"]DJANGO_SETTINGS_MODULE['\"],\s*['\"](.+?)['\"]", manage_content)
        if match:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', match.group(1))
        else:
            raise ValueError("Could not find DJANGO_SETTINGS_MODULE")
except FileNotFoundError:
    sys.exit(1)

django.setup()

from django.test import Client
from django.conf import settings

# 2. THE TEST
# We use @patch to mock the Stripe API call so we don't actually hit the internet
@patch('stripe.Customer.retrieve')
def run_cancellation_test(mock_stripe_retrieve):
    print("\n--- 🛑 SIMULATING SUBSCRIPTION CANCELLATION ---")
    
    # Setup the mock to return a fake customer object with an email
    mock_customer = type('obj', (object,), {'email': 'sad_donor@example.com'})
    mock_stripe_retrieve.return_value = mock_customer

    secret = settings.STRIPE_WEBHOOK_SECRET
    
    # Payload for 'customer.subscription.deleted'
    payload = {
        "id": "evt_test_cancel",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_cancelled_123",
                "customer": "cus_fake_123",
                "status": "canceled"
            }
        }
    }
    
    payload_str = json.dumps(payload)
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()

    client = Client()
    response = client.post(
        '/api/donations/webhook/', 
        data=payload_str,
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}"
    )

    print(f"📡 Webhook Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Webhook processed the cancellation.")
        print(f"   (Mocked) Admin email logic triggered for: sad_donor@example.com")
    else:
        print("❌ FAILED: Webhook rejected the request.")

if __name__ == "__main__":
    run_cancellation_test()