#!/usr/bin/env python
import os
import sys

# turn on random occupancy for this test run so we can validate it behaves correctly
os.environ.setdefault('RANDOMIZE_OCCUPANCY', 'True')
# Setup Django BEFORE importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Test the parking status endpoint
client = Client()

# First, login
print("Testing Parking Status Page...")
print("=" * 60)

# Try to get the page without login (should redirect)
print("\n1. Testing without authentication:")
response = client.get('/parking-lot-status/')
print(f"   Status Code: {response.status_code}")
print(f"   Expected: 302 (Redirect to login)")

# Login with test user
print("\n2. Logging in as user...")
try:
    user = User.objects.get(username='user')
    print(f"   Found user: {user.username}")
except User.DoesNotExist:
    print("   User not found, creating test user...")
    user = User.objects.create_user(username='user', email='user@test.com', password='UserPass@123')

# Login
login_success = client.login(username='user', password='UserPass@123')
print(f"   Login Success: {login_success}")

# create a temporary test lot so the filter has something to remove
from parkingapp.models import ParkingLot
ParkingLot.objects.get_or_create(lot_name='Test Demo Lot', defaults={'total_spots':10})

# Try accessing the page after login
print("\n3. Accessing parking status page with authentication:")
response = client.get('/parking-lot-status/')
print(f"   Status Code: {response.status_code}")
print(f"   Template Used: {response.template_name if hasattr(response, 'template_name') else 'N/A'}")

if response.status_code == 200:
    print("   ✅ Page loaded successfully!")
    
    # Check context data
    context = response.context
    if context:
        # note may be present when test lots were removed by filter
        if 'note' in context:
            print(f"   📝 Note shown: {context['note']}")
            assert 'hidden' in context['note'].lower()
        if 'parking_lots' in context:
            lots = context['parking_lots']
            print(f"   📍 Found {len(lots)} parking lots")
            for lot in lots[:3]:  # Show first 3
                print(f"      - {lot.get('lot_name')}: {lot.get('occupied_spots')}/{lot.get('total_spots')} occupied ({lot.get('occupancy_rate')}%)")
                # validate occupancy bounds and math
                if lot.get('total_spots'):
                    occ_rate = float(lot.get('occupancy_rate'))
                    assert 20 <= occ_rate <= 85, f"lot {lot.get('lot_name')} occupancy {occ_rate}% outside expected range"
                    assert lot.get('occupied_spots') + lot.get('available_spots') == lot.get('total_spots')
        
        if 'total_stats' in context:
            stats = context['total_stats']
            print(f"   📊 Overall Stats:")
            print(f"      - Total Spots: {stats.get('total')}")
            print(f"      - Occupied: {stats.get('occupied')}")
            print(f"      - Available: {stats.get('available')}")
            print(f"      - Occupancy Rate: {stats.get('occupancy_rate')}%")
            if stats.get('total'):
                overall_rate = float(stats.get('occupancy_rate'))
                assert 20 <= overall_rate <= 85, f"overall occupancy rate {overall_rate}% outside expected range"
else:
    print(f"   ❌ Page failed to load: {response.status_code}")
    print(f"   Response Content: {response.content[:500]}")

print("\n" + "=" * 60)
print("Test completed!")
