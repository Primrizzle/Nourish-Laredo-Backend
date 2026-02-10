import os
import sys
import json
import time
import hmac
import hashlib
import django

# 1. DYNAMIC PATH SETUP
# This finds the parent directory (Nourish-Laredo-Backend) 
# and adds it to the system path so Django can see your 'core' app.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 2. INITIALIZE DJANGO
# Check your project folder name. If it's not 'nourish_laredo_backend', 
# change it to the name of the folder containing settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# 3. NOW WE CAN IMPORT DJANGO TOOLS
from django.test import Client
from django.conf import settings
from core.models import Donation, Person

def run_recurring_test():
    print("\n--- 🔄 SIMULATING RECURRING PAYMENT WEBHOOK ---")
    
    FAKE_INVOICE_ID = "in_test_recurring_999"
    TEST_EMAIL = "subscriber@example.com"
    secret = settings.STRIPE_WEBHOOK_SECRET
    
    # Pre-test cleanup
    Donation.objects.filter(processor_reference_id=FAKE_INVOICE_ID).delete()

    # Construct the Stripe Invoice Payload
    # This simulates what Stripe sends every month for a subscription
    payload = {
        "id": "evt_test_recurring",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": FAKE_INVOICE_ID,
                "amount_paid": 2500, # $25.00
                "customer_email": TEST_EMAIL,
                "customer_name": "Recurring Donor",
                "subscription": "sub_12345abc",
                "status": "paid"
            }
        }
    }
    
    payload_str = json.dumps(payload)
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()

    # Trigger the Webhook
    client = Client()
    # We use the correct path we verified earlier
    response = client.post(
        '/api/donations/webhook/', 
        data=payload_str,
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}"
    )

    print(f"📡 Webhook Status Code: {response.status_code}")
    
    # Final Verification
    donation_exists = Donation.objects.filter(processor_reference_id=FAKE_INVOICE_ID).exists()
    person_exists = Person.objects.filter(email=TEST_EMAIL).exists()

    if donation_exists and person_exists:
        print("✅ SUCCESS: Donation and Person records created correctly!")
    else:
        if not donation_exists: print("❌ FAILED: Donation record missing.")
        if not person_exists: print("❌ FAILED: Person record missing.")

if __name__ == "__main__":
    run_recurring_test()