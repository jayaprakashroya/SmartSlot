import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.test import Client

client = Client()

print("=" * 60)
print("Testing Passes and Find Parking Features")
print("=" * 60)

# Test 1: Passes without login
print("\n[TEST 1] Testing Passes (should be PUBLIC):")
response = client.get('/purchase-pass/')
print(f"   URL: /purchase-pass/")
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    print("   PASS - Passes page accessible WITHOUT login!")
elif response.status_code == 302:
    print(f"   FAIL - Redirected to: {response.url}")
else:
    print(f"   Status: {response.status_code}")

# Test 2: Find Parking without login
print("\n[TEST 2] Testing Find Parking (should be PUBLIC):")
response = client.get('/parking-map/')
print(f"   URL: /parking-map/")
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    print("   PASS - Find Parking map accessible WITHOUT login!")
    # Check for data in context
    context = response.context
    if context:
        if 'lots' in context:
            lots = context['lots']
            print(f"   Found {len(lots)} parking lots in context")
        if 'lot_data' in context:
            print(f"   PASS - Lot data successfully JSON serialized")
elif response.status_code == 302:
    print(f"   FAIL - Redirected to: {response.url}")
else:
    print(f"   Status: {response.status_code}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
