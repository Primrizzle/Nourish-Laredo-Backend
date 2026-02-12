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
from core.models import VolunteerProfile

def run_volunteer_test():
    print("\n--- 🧡 SIMULATING VOLUNTEER SIGN-UP ---")
    
    # Test Data
    test_email = "jane.doe@example.com"
    test_name = "Jane Doe"
    
    # Cleanup previous tests to ensure a fresh run
    VolunteerProfile.objects.filter(email=test_email).delete()

    # Payload adjusted to match your Backend & Frontend
    payload = {
        "full_name": "Jane Doe",       # FIXED: Matches backend requirement
        "email": "jane.doe@example.com",
        "phone": "(956) 555-9876",
        "availability": "Weekends",    # Added to match your form
        "message": "I am excited to help!" # Note: Backend likely expects 'message', not 'motivation'
    }

    # Hit the API (Use the correct URL we found in the logs)
    client = Client()
    response = client.post(
        '/api/volunteer-signup/', 
        data=json.dumps(payload),
        content_type='application/json'
    )

    print(f"📡 API Status Code: {response.status_code}")
    
    # Verify Database Persistence
    try:
        volunteer = VolunteerProfile.objects.get(email=test_email)
        print(f"✅ SUCCESS: Volunteer Profile created for '{volunteer.full_name}'")
    except VolunteerProfile.DoesNotExist:
        print("❌ FAILED: Volunteer was not saved to the database.")

    if response.status_code == 201:
        print("✅ SUCCESS: View returned 201 Created.")
        print("\n👇 CHECK TERMINAL FOR EMAILS (Admin Notification + Volunteer Welcome) 👇\n")
    else:
        print(f"❌ FAILED: Received {response.status_code}. Response: {response.content}")

if __name__ == "__main__":
    run_volunteer_test()