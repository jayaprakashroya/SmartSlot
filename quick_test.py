import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'ParkingProject.settings'

import django
django.setup()

from django.test import Client

print("Testing Passes and Find Parking...")

c = Client()

# Test passes
resp1 = c.get('/purchase-pass/')
print(f"Passes: {resp1.status_code}")

# Test find parking
resp2 = c.get('/parking-map/')
print(f"Find Parking: {resp2.status_code}")

if resp1.status_code == 200 and resp2.status_code == 200:
    print("SUCCESS - Both accessible!")
else:
    print("FAILED - Some features need login")
