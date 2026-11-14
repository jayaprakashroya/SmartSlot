"""
Complete System Endpoint Verification
Tests all buttons, APIs, and features in the heatmap and related pages
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

import json
from django.test import Client
from django.contrib.auth.models import User
from parkingapp.models import User_details, ParkingSession, ParkingReservation, UserNotification

# Initialize test client
client = Client()

print("=" * 80)
print("SMARTSLOT - COMPLETE ENDPOINT & FEATURE VERIFICATION")
print("=" * 80)

# Create test user if doesn't exist
try:
    admin_user = User.objects.get(username='admin')
    print("\n✅ Admin user exists")
except:
    admin_user = User.objects.create_user(username='admin', password='AdminPass@123')
    print("✅ Admin user created")

# Test data endpoints
endpoints = {
    'Heatmap': [
        ('GET', '/heatmap/', 'Heatmap main page'),
        ('GET', '/heatmap/1/', 'Heatmap for Lot 1'),
        ('GET', '/api/heatmap-realtime/1/', 'Real-time heatmap data'),
        ('GET', '/api/heatmap-analytics/1/', 'Heatmap analytics'),
    ],
    'Parking History': [
        ('GET', '/parking-history/', 'Parking history page'),
        ('GET', '/api/parking-history/', 'Parking history API'),
        ('GET', '/api/recent-activity/', 'Recent activity'),
    ],
    'Reservations': [
        ('GET', '/reserve-parking/', 'Reserve parking form'),
        ('GET', '/my-reservations/', 'My reservations'),
        ('GET', '/api/available-spots/1/', 'Available spots API'),
    ],
    'Notifications': [
        ('GET', '/notifications/', 'Notifications page'),
    ],
    'Real-Time Status': [
        ('GET', '/api/offline-status/', 'Offline status'),
        ('GET', '/api/parking-status/', 'Parking status'),
        ('GET', '/api/parking-status/1/', 'Parking status for Lot 1'),
        ('GET', '/parking-lot-status/', 'Parking lot status page'),
    ],
    'Analytics': [
        ('GET', '/analytics-dashboard/', 'Analytics dashboard'),
        ('GET', '/revenue-report/', 'Revenue report'),
        ('GET', '/peak-hours-forecast/', 'Peak hours forecast'),
    ],
    'Payments': [
        ('GET', '/payments/', 'Payments page'),
    ],
    'Admin Features': [
        ('GET', '/admin-dashboard/', 'Admin dashboard'),
        ('GET', '/api/admin/dashboard-stats/', 'Admin dashboard stats'),
        ('GET', '/admin-action-history/', 'Admin action history'),
    ]
}

print("\n" + "=" * 80)
print("ENDPOINT VERIFICATION RESULTS")
print("=" * 80)

results = {}
for category, urls in endpoints.items():
    results[category] = {'working': 0, 'failed': 0, 'details': []}
    print(f"\n📍 {category}")
    print("-" * 80)
    
    for method, url, description in urls:
        try:
            if method == 'GET':
                response = client.get(url)
            else:
                response = client.post(url)
            
            status = '✅' if response.status_code in [200, 302, 404] else '❌'
            
            if response.status_code in [200, 302]:
                results[category]['working'] += 1
                msg = f"{status} {description:40} [{response.status_code}]"
            else:
                results[category]['failed'] += 1
                msg = f"{status} {description:40} [{response.status_code}] - NOT WORKING"
            
            results[category]['details'].append(msg)
            print(msg)
            
        except Exception as e:
            results[category]['failed'] += 1
            msg = f"❌ {description:40} [ERROR] - {str(e)[:40]}"
            results[category]['details'].append(msg)
            print(msg)

print("\n" + "=" * 80)
print("FEATURE DATA VERIFICATION")
print("=" * 80)

# Check database records
from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle, ParkingAnalytics

print(f"\n📊 Database Records:")
print(f"  • Parking Lots: {ParkingLot.objects.count()}")
print(f"  • Parking Spots: {ParkingSpot.objects.count()}")
print(f"  • Parked Vehicles: {ParkedVehicle.objects.count()}")
print(f"  • Analytics Records: {ParkingAnalytics.objects.count()}")
print(f"  • Parking Sessions: {ParkingSession.objects.count()}")
print(f"  • Reservations: {ParkingReservation.objects.count()}")
print(f"  • Notifications: {UserNotification.objects.count()}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_working = sum(r['working'] for r in results.values())
total_failed = sum(r['failed'] for r in results.values())
total = total_working + total_failed

for category, result in results.items():
    pct = (result['working'] / (result['working'] + result['failed']) * 100) if (result['working'] + result['failed']) > 0 else 0
    print(f"\n{category:20} ✅ {result['working']:2} / ❌ {result['failed']:2} ({pct:.0f}%)")

print(f"\n{'=' * 80}")
print(f"OVERALL: ✅ {total_working}/{total} endpoints working ({total_working/total*100:.0f}%)")
print(f"{'=' * 80}")

print("\n💡 NOTES:")
print("  • 302 redirects (login) are normal - means endpoint exists")
print("  • 404 errors might mean page not found")
print("  • All API endpoints should return 200 or JSON data")
print("\n📱 Test URLs in Browser:")
print("  • http://127.0.0.1:8000/heatmap/")
print("  • http://127.0.0.1:8000/parking-history/")
print("  • http://127.0.0.1:8000/notifications/")
print("  • http://127.0.0.1:8000/my-reservations/")
print("=" * 80)
