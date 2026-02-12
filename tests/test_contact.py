import os
import sys
import json
import time
import hmac
import hashlib
import django
import re

# 1. SETUP PATHS & SETTINGS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Auto-detect settings module from manage.py
try:
    with open(os.path.join(BASE_DIR, 'manage.py'), 'r') as f:
        manage_content = f.read()
        match = re.search(r"['\"]DJANGO_SETTINGS_MODULE['\"],\s*['\"](.+?)['\"]", manage_content)
        if match:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', match.group(1))
        else:
            raise ValueError("Could not find DJANGO_SETTINGS_MODULE")
except FileNotFoundError:
    print("❌ Error: Run this from the project root.")
    sys.exit(1)

django.setup()

from django.test import Client
from core.models import ContactMessage

def run_contact_test():
    print("\n--- ✉️  SIMULATING CONTACT FORM SUBMISSION ---")
    
    # Test Data
    test_name = "Test Submitter"
    test_email = "tester@example.com"
    test_subject = "Inquiry: Holiday Drive"
    test_message = "Hello! I am testing the contact form backend. Please verify if you see this in the admin panel."

    # Pre-test cleanup 
    ContactMessage.objects.filter(email=test_email).delete()

    # Payload
    payload = {
        "name": test_name,
        "email": test_email,
        "subject": test_subject,
        "message": test_message
    }

    # Use Django's Test Client to hit the endpoint
    client = Client()
    response = client.post(
        '/api/contact/', 
        data=json.dumps(payload),
        content_type='application/json'
    )

    print(f"📡 API Status Code: {response.status_code}")
    
    # Verify Database entry
    try:
        msg = ContactMessage.objects.get(email=test_email)
        print(f"✅ SUCCESS: Message saved in database (ID: {msg.id})")
        print(f"   Subject: {msg.subject}")
    except ContactMessage.DoesNotExist:
        print("❌ FAILED: Message was not saved to the database.")

    if response.status_code == 201:
        print("✅ SUCCESS: View returned 201 Created.")
    else:
        print(f"❌ FAILED: Received {response.status_code}. Response: {response.content}")

if __name__ == "__main__":
    run_contact_test()