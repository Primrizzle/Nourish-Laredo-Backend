import os
import sys
import json
import django
import re

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
    print("❌ Error: Run this from the project root.")
    sys.exit(1)

django.setup()

from django.test import Client
from core.models import PartnerInquiry

def run_partner_test():
    print("\n--- 🤝 SIMULATING PARTNER INQUIRY ---")
    
    # Test Data
    test_org = "Bob's Burgers Laredo"
    test_contact = "Bob Belcher"
    test_email = "bob@bobsburgers.com"
    
    # Cleanup previous tests
    PartnerInquiry.objects.filter(email=test_email).delete()

    # Payload (Matches your React Form)
    payload = {
        "organization_name": test_org,
        "contact_name": test_contact,
        "email": test_email,
        "phone": "(956) 555-0199",
        "website": "https://bobsburgers.com",
        "partnership_type": "in_kind", # Value from your select dropdown
        "message": "We would like to donate 50 burgers for your next youth event."
    }

    # Hit the API
    client = Client()
    response = client.post(
        '/api/partners/inquiry/', 
        data=json.dumps(payload),
        content_type='application/json'
    )

    print(f"📡 API Status Code: {response.status_code}")
    
    # Verify Database
    try:
        inquiry = PartnerInquiry.objects.get(email=test_email)
        print(f"✅ SUCCESS: Inquiry saved for '{inquiry.organization_name}'")
        print(f"   Type: {inquiry.get_partnership_type_display()}")
    except PartnerInquiry.DoesNotExist:
        print("❌ FAILED: Inquiry was not saved to the database.")

    if response.status_code == 201:
        print("✅ SUCCESS: View returned 201 Created.")
        print("\n👇 CHECK BELOW FOR TWO EMAILS (Admin Notification + User Confirmation) 👇\n")
    else:
        print(f"❌ FAILED: Received {response.status_code}. Response: {response.content}")

if __name__ == "__main__":
    run_partner_test()