"""
Test authentication flow for parking status
Verify: logged-in users can access, non-logged-in users get redirected to login
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from parkingapp.models import ParkingLot

print("=" * 70)
print("🧪 AUTHENTICATION TEST FOR PARKING STATUS")
print("=" * 70)

client = Client()

# Check if parking lots exist
print("\n1️⃣ Checking database...")
parking_lots_count = ParkingLot.objects.count()
print(f"   📍 Parking Lots in DB: {parking_lots_count}")

# Test 1: Access without authentication
print("\n2️⃣ Testing WITHOUT authentication (non-logged-in user):")
response = client.get('/parking-lot-status/')
print(f"   Status Code: {response.status_code}")
print(f"   Expected: 302 (Redirect to login)")
if response.status_code == 302:
    print(f"   ✅ Correctly redirected to: {response.url}")
else:
    print(f"   ❌ ERROR: Expected 302, got {response.status_code}")

# Test 2: Check/create test user
print("\n3️⃣ Setting up test user:")
try:
    user = User.objects.get(username='user')
    print(f"   ✅ Found existing user: {user.username}")
except User.DoesNotExist:
    user = User.objects.create_user(
        username='user',
        email='user@test.com',
        password='UserPass@123'
    )
    print(f"   ✅ Created new user: {user.username}")

# Test 3: Login
print("\n4️⃣ Attempting login:")
login_success = client.login(username='user', password='UserPass@123')
print(f"   Login Success: {login_success}")

if not login_success:
    print("   ❌ Login failed! Trying with email...")
    # Try with email
    login_success = client.login(username='user@test.com', password='UserPass@123')
    print(f"   Email Login Success: {login_success}")

# Test 4: Access WITH authentication
print("\n5️⃣ Testing WITH authentication (logged-in user):")
response = client.get('/parking-lot-status/')
print(f"   Status Code: {response.status_code}")

if response.status_code == 200:
    print(f"   ✅ Page accessed successfully!")
    
    # Check context
    if hasattr(response, 'context') and response.context:
        context = response.context
        
        if 'parking_lots' in context:
            lots = context['parking_lots']
            print(f"\n   📊 Parking Lots Data:")
            print(f"      - Total lots: {len(lots)}")
            
            for i, lot in enumerate(lots[:2], 1):
                print(f"      {i}. {lot.get('lot_name')}")
                print(f"         Total: {lot.get('total_spots')} spots")
                print(f"         Occupied: {lot.get('occupied_spots')} spots")
                print(f"         Available: {lot.get('available_spots')} spots")
                print(f"         Rate: {lot.get('occupancy_rate')}%")
        
        if 'total_stats' in context:
            stats = context['total_stats']
            print(f"\n   📈 Overall Statistics:")
            print(f"      - Total Spots: {stats.get('total')}")
            print(f"      - Occupied: {stats.get('occupied')}")
            print(f"      - Available: {stats.get('available')}")
            print(f"      - Occupancy Rate: {stats.get('occupancy_rate')}%")
else:
    print(f"   ❌ Page failed! Status: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirected to: {response.url}")
        print(f"   🔍 Session data: {dict(client.session)}")

# Test 5: Session verification
print("\n6️⃣ Verifying session:")
if '_auth_user_id' in client.session:
    print(f"   ✅ Session is active for user ID: {client.session['_auth_user_id']}")
else:
    print(f"   ❌ No active session found")
    print(f"   Session keys: {list(client.session.keys())}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETED")
print("=" * 70)
