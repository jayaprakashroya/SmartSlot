#!/usr/bin/env python
"""
Complete Endpoint & Error Testing
Tests all endpoints and identifies errors
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from parkingapp.models import *
import json

client = Client()

# Create test user
try:
    admin_user = User.objects.get(username='admin')
except:
    admin_user = User.objects.create_user(username='admin', password='AdminPass@123', email='admin@smartparking.com')

print("\n" + "="*80)
print("SMARTSLOT - COMPLETE ENDPOINT ERROR CHECK & DIAGNOSIS")
print("="*80)

# Define all endpoints to test
tests = {
    'HEATMAP FEATURES': [
        ('/heatmap/', 'GET', 'Heatmap main page'),
        ('/heatmap/1/', 'GET', 'Heatmap for Lot 1'),
        ('/api/heatmap-realtime/1/', 'GET', 'Real-time heatmap API'),
        ('/api/heatmap-analytics/1/', 'GET', 'Heatmap analytics API'),
    ],
    'PARKING MANAGEMENT': [
        ('/parking-history/', 'GET', 'Parking history page'),
        ('/api/parking-history/', 'GET', 'Parking history API'),
        ('/parking-lot-status/', 'GET', 'Parking lot status page'),
        ('/parking-lot-status/1/', 'GET', 'Parking lot status for Lot 1'),
        ('/api/parking-status/', 'GET', 'Parking status API'),
        ('/api/parking-status/1/', 'GET', 'Parking status for Lot 1'),
    ],
    'RESERVATIONS': [
        ('/reserve-parking/', 'GET', 'Reserve parking form'),
        ('/my-reservations/', 'GET', 'My reservations page'),
        ('/api/available-spots/1/', 'GET', 'Available spots API'),
    ],
    'NOTIFICATIONS': [
        ('/notifications/', 'GET', 'Notifications page'),
    ],
    'REAL-TIME & OFFLINE': [
        ('/api/offline-status/', 'GET', 'Offline status API'),
        ('/api/parking-status/', 'GET', 'Parking status real-time'),
    ],
    'ADMIN FEATURES': [
        ('/admin-dashboard/', 'GET', 'Admin dashboard'),
        ('/api/admin/dashboard-stats/', 'GET', 'Admin dashboard stats API'),
        ('/admin-action-history/', 'GET', 'Admin action history'),
    ],
    'ANALYTICS': [
        ('/analytics-dashboard/', 'GET', 'Analytics dashboard'),
        ('/revenue-report/', 'GET', 'Revenue report'),
        ('/peak-hours-forecast/', 'GET', 'Peak hours forecast'),
    ],
    'PAYMENTS': [
        ('/payments/', 'GET', 'Payments page'),
    ],
    'SEARCH & FIND': [
        ('/find-my-car/', 'GET', 'Find my car page'),
        ('/search-by-phone/', 'GET', 'Search by phone'),
    ],
    'ADVANCED FEATURES': [
        ('/parking-map/', 'GET', 'Parking map'),
        ('/find-my-vehicle/', 'GET', 'Find my vehicle'),
    ]
}

results = {}
errors_found = []

for category, endpoints in tests.items():
    results[category] = {'total': 0, 'working': 0, 'errors': 0, 'details': []}
    print(f"\n{'='*80}")
    print(f"📍 {category}")
    print('='*80)
    
    for url, method, description in endpoints:
        results[category]['total'] += 1
        try:
            if method == 'GET':
                response = client.get(url)
            else:
                response = client.post(url)
            
            status_code = response.status_code
            
            # Check if response is successful or redirect (auth required)
            if status_code == 200:
                status = '✅'
                results[category]['working'] += 1
                msg = f"{status} {description:40} [{status_code}]"
            elif status_code == 302:  # Redirect (normal for auth)
                status = '⚠️'
                results[category]['working'] += 1
                msg = f"{status} {description:40} [{status_code}] REDIRECT"
            elif status_code == 404:
                status = '❌'
                results[category]['errors'] += 1
                msg = f"{status} {description:40} [{status_code}] PAGE NOT FOUND"
                errors_found.append({'url': url, 'status': 404, 'desc': description})
            elif status_code == 500:
                status = '🔴'
                results[category]['errors'] += 1
                msg = f"{status} {description:40} [{status_code}] SERVER ERROR"
                errors_found.append({'url': url, 'status': 500, 'desc': description})
            else:
                status = '⚠️'
                msg = f"{status} {description:40} [{status_code}]"
            
            results[category]['details'].append(msg)
            print(msg)
            
        except Exception as e:
            results[category]['errors'] += 1
            msg = f"❌ {description:40} [EXCEPTION] - {str(e)[:50]}"
            results[category]['details'].append(msg)
            print(msg)
            errors_found.append({'url': url, 'error': str(e), 'desc': description})

# Summary
print(f"\n{'='*80}")
print("📊 SUMMARY REPORT")
print('='*80)

total_endpoints = sum(r['total'] for r in results.values())
total_working = sum(r['working'] for r in results.values())
total_errors = sum(r['errors'] for r in results.values())

for category, result in results.items():
    pct = (result['working'] / result['total'] * 100) if result['total'] > 0 else 0
    print(f"\n{category:25} ✅ {result['working']:2} / ❌ {result['errors']:2} ({pct:.0f}%)")

print(f"\n{'='*80}")
print(f"OVERALL RESULT: ✅ {total_working}/{total_endpoints} endpoints working ({total_working/total_endpoints*100:.1f}%)")
print(f"ERRORS FOUND: {total_errors}")
print('='*80)

# Database verification
print(f"\n{'='*80}")
print("🗄️  DATABASE VERIFICATION")
print('='*80)

print(f"\n✅ Parking Lots: {ParkingLot.objects.count()}")
print(f"✅ Parking Spots: {ParkingSpot.objects.count()}")
print(f"✅ Parked Vehicles: {ParkedVehicle.objects.count()}")
print(f"✅ Notifications: {UserNotification.objects.count()}")
print(f"✅ Reservations: {ParkingReservation.objects.count()}")
print(f"✅ Analytics: {ParkingAnalytics.objects.count()}")
print(f"✅ Pricing Rules: {PricingRule.objects.count()}")

# Error details
if errors_found:
    print(f"\n{'='*80}")
    print(f"🔴 DETAILED ERROR REPORT ({len(errors_found)} errors)")
    print('='*80)
    for i, err in enumerate(errors_found, 1):
        print(f"\n{i}. {err['desc']}")
        print(f"   URL: {err['url']}")
        if 'status' in err:
            print(f"   Status Code: {err['status']}")
        if 'error' in err:
            print(f"   Error: {err['error'][:100]}")
else:
    print(f"\n{'='*80}")
    print("✅ NO CRITICAL ERRORS FOUND!")
    print('='*80)

print(f"\n{'='*80}")
print("✅ ENDPOINT TESTING COMPLETE")
print('='*80)
