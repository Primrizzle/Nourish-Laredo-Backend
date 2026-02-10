import os
import django
import json
import time
import hmac
import hashlib

# 1. SETUP DJANGO ENVIRONMENT
# CHANGE 'nourishlaredo.settings' to your actual project name!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from django.test import Client
from core.models import Donation, Person  # Update 'donations' to your app name

def run_test():
    print("--- STARTING WEBHOOK TEST ---")

    # 2. SETUP DATA
    # We create a fake session ID that matches what we send in the webhook
    FAKE_SESSION_ID = "cs_test_123456789"
    
    # Clean up previous test runs
    Donation.objects.filter(processor_reference_id=FAKE_SESSION_ID).delete()
    Person.objects.filter(email="test_donor@example.com").delete()

    # Create a Pending Donation
    donation = Donation.objects.create(
        amount=5000,
        currency="USD",
        status="pending",
        processor_reference_id=FAKE_SESSION_ID
    )
    print(f"✅ Created Pending Donation: ID {donation.id} (Status: {donation.status})")

    # 3. CREATE PAYLOAD (What Stripe sends)
    payload_data = {
        "id": "evt_test_webhook",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": FAKE_SESSION_ID,
                "customer_details": {
                    "email": "test_donor@example.com",
                    "name": "Jane Doe"
                }
            }
        }
    }
    payload_json = json.dumps(payload_data)

    # 4. GENERATE SIGNATURE (Simulate Stripe Security)
    # We must sign the payload using your local secret to pass the security check
    secret = settings.STRIPE_WEBHOOK_SECRET
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload_json}"
    
    # HMAC SHA256 Signature
    signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=signed_payload.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    header = f"t={timestamp},v1={signature}"

    # 5. SEND REQUEST TO VIEW
    c = Client()
    # Ensure this URL matches what is in your urls.py
    response = c.post(
        '/api/donations/webhook/', 
        data=payload_json, 
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE=header
    )

    print(f"📡 Webhook Response Code: {response.status_code}")

    if response.status_code != 200:
        print("❌ FAILED: Webhook did not return 200 OK.")
        print("   Check if STRIPE_WEBHOOK_SECRET in settings matches what you used here.")
        return

    # 6. VERIFY DATABASE UPDATES
    donation.refresh_from_db()
    print(f"🔍 Donation Status: {donation.status}")

    if donation.status == 'succeeded':
        print("✅ SUCCESS: Donation marked as succeeded.")
    else:
        print("❌ FAILED: Donation status is still pending.")

    # Check Person
    try:
        person = Person.objects.get(email="test_donor@example.com")
        print(f"✅ SUCCESS: Person created: {person.first_name} {person.last_name}")
        
        if donation.person == person:
            print("✅ SUCCESS: Donation is successfully linked to Person.")
        else:
            print("❌ FAILED: Donation is NOT linked to Person.")
            
    except Person.DoesNotExist:
        print("❌ FAILED: Person was not created.")

if __name__ == '__main__':
    run_test()