import os
import django

# ensure randomization is active for this run
os.environ.setdefault('RANDOMIZE_OCCUPANCY', 'True')

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
            total = lot.get('total_spots')
            occupied = lot.get('occupied_spots')
            rate = (occupied / total * 100) if total else 0
            print(f"   - {lot.get('lot_name')}: {occupied}/{total} ({rate:.1f}%)")
            # sanity assertions when randomization is enabled
            assert occupied <= total, "occupied count cannot exceed total"
            if total:
                assert 20 <= rate <= 85, f"occupancy rate {rate} not within expected random range"
else:
    print(f"❌ Status {response.status_code}")
    print(f"Response: {response.content[:200]}")
