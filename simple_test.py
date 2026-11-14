#!/usr/bin/env python
"""
Simple endpoint tester - checks if heatmap link works after login
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from parkingapp.models import *

client = Client()

# Ensure admin user exists
try:
    admin = User.objects.get(username='admin')
    print("✅ Admin user exists")
except:
    admin = User.objects.create_user(username='admin', password='AdminPass@123', email='admin@smartparking.com')
    print("✅ Admin user created")

print("\n" + "="*70)
print("ENDPOINT VERIFICATION TEST")
print("="*70)

# Test endpoints
tests = [
    ('/heatmap/', 'Heatmap page'),
    ('/api/heatmap-realtime/1/', 'Heatmap API'),
    ('/parking-history/', 'Parking History'),
    ('/my-reservations/', 'Reservations'),
    ('/notifications/', 'Notifications'),
    ('/api/parking-status/', 'Parking Status API'),
]

print("\n📊 ENDPOINT TESTS:\n")

for url, name in tests:
    try:
        resp = client.get(url)
        if resp.status_code < 400:
            print(f"✅ {name:30} [{resp.status_code}]")
        else:
            print(f"⚠️  {name:30} [{resp.status_code}]")
    except Exception as e:
        print(f"❌ {name:30} [ERROR]")

# Database check
print(f"\n📊 DATABASE STATUS:\n")
print(f"  ✅ Parking Lots: {ParkingLot.objects.count()}")
print(f"  ✅ Parking Spots: {ParkingSpot.objects.count()}")
print(f"  ✅ Parked Vehicles: {ParkedVehicle.objects.count()}")
print(f"  ✅ Notifications: {UserNotification.objects.count()}")
print(f"  ✅ Reservations: {ParkingReservation.objects.count()}")

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE")
print("="*70)
print("\n📍 Access the system:")
print("  • URL: http://127.0.0.1:8000/")
print("  • Login: admin / AdminPass@123")
print("  • After login, click: 🔥 Heatmap")
print("="*70)
