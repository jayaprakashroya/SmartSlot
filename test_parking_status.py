#!/usr/bin/env python
import os
import sys

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
        if 'parking_lots' in context:
            lots = context['parking_lots']
            print(f"   📍 Found {len(lots)} parking lots")
            for lot in lots[:3]:  # Show first 3
                print(f"      - {lot.get('lot_name')}: {lot.get('occupied_spots')}/{lot.get('total_spots')} occupied ({lot.get('occupancy_rate')}%)")
        
        if 'total_stats' in context:
            stats = context['total_stats']
            print(f"   📊 Overall Stats:")
            print(f"      - Total Spots: {stats.get('total')}")
            print(f"      - Occupied: {stats.get('occupied')}")
            print(f"      - Available: {stats.get('available')}")
            print(f"      - Occupancy Rate: {stats.get('occupancy_rate')}%")
else:
    print(f"   ❌ Page failed to load: {response.status_code}")
    print(f"   Response Content: {response.content[:500]}")

print("\n" + "=" * 60)
print("Test completed!")
