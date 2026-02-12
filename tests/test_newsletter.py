import os
import sys
import json
import django
import re

# 1. SETUP PATHS
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
from core.models import NewsletterSubscriber

def run_newsletter_test():
    print("\n--- 📧 SIMULATING NEWSLETTER SIGN-UP ---")
    
    test_email = "subscriber@example.com"
    
    # 1. Cleanup: Remove if exists so we can test a fresh signup
    NewsletterSubscriber.objects.filter(email=test_email).delete()

    client = Client()
    
    # 2. Test First Signup (Should be 201 Created)
    print(f"👉 Attempt 1: Subscribing {test_email}...")
    response = client.post(
        '/api/newsletter/subscribe/', 
        data=json.dumps({"email": test_email}),
        content_type='application/json'
    )

    if response.status_code == 201:
        print("✅ SUCCESS: First subscription worked (201 Created).")
    else:
        print(f"❌ FAILED: Expected 201, got {response.status_code}")
        print(response.content)

    # 3. Test Duplicate Signup (Should be 200 OK with message)
    print(f"\n👉 Attempt 2: Subscribing {test_email} AGAIN (Duplicate test)...")
    response_dup = client.post(
        '/api/newsletter/subscribe/', 
        data=json.dumps({"email": test_email}),
        content_type='application/json'
    )

    if response_dup.status_code == 200:
        print("✅ SUCCESS: Handled duplicate gracefully (200 OK).")
        print(f"   Message: {response_dup.json().get('message')}")
    else:
        print(f"❌ FAILED: Expected 200 for duplicate, got {response_dup.status_code}")
        print(response_dup.content)

if __name__ == "__main__":
    run_newsletter_test()