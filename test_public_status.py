import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.test import Client

client = Client()

# Test without login
print("Testing Parking Status (No Login)...")
response = client.get('/parking-lot-status/')
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("✅ Parking Status is now ACCESSIBLE WITHOUT LOGIN!")
    context = response.context
    if context and 'parking_lots' in context:
        lots = context['parking_lots']
        print(f"   Found {len(lots)} parking lots")
        for lot in lots[:2]:
            print(f"   - {lot.get('lot_name')}: {lot.get('occupied_spots')}/{lot.get('total_spots')}")
else:
    print(f"❌ Status {response.status_code}")
    print(f"Response: {response.content[:200]}")
