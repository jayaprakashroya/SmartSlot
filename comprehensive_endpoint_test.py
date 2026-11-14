#!/usr/bin/env python
"""
Comprehensive Endpoint Testing & Error Detection
Tests all endpoints and identifies errors for fixing
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import json
import traceback

# Create test client
client = Client()

# Create/get test user
try:
    user = User.objects.get(username='admin')
except:
    user = User.objects.create_user(username='admin', password='AdminPass@123')

# Login for protected endpoints
client.login(username='admin', password='AdminPass@123')

# All endpoints to test
endpoints = {
    'Heatmap': {
        'GET /heatmap/': '/heatmap/',
        'GET /heatmap/1/': '/heatmap/1/',
        'GET /api/heatmap-realtime/1/': '/api/heatmap-realtime/1/',
        'GET /api/heatmap-analytics/1/': '/api/heatmap-analytics/1/',
    },
    'Parking Management': {
        'GET /parking-history/': '/parking-history/',
        'GET /parking-lot-status/': '/parking-lot-status/',
        'GET /parking-lot-status/1/': '/parking-lot-status/1/',
        'GET /api/parking-status/': '/api/parking-status/',
        'GET /api/parking-status/1/': '/api/parking-status/1/',
        'GET /api/offline-status/': '/api/offline-status/',
        'GET /api/recent-activity/': '/api/recent-activity/',
    },
    'Reservations': {
        'GET /reserve-parking/': '/reserve-parking/',
        'GET /my-reservations/': '/my-reservations/',
        'GET /api/available-spots/1/': '/api/available-spots/1/',
    },
    'Notifications': {
        'GET /notifications/': '/notifications/',
    },
    'Analytics': {
        'GET /analytics-dashboard/': '/analytics-dashboard/',
        'GET /revenue-report/': '/revenue-report/',
        'GET /peak-hours-forecast/': '/peak-hours-forecast/',
    },
    'Payments': {
        'GET /payments/': '/payments/',
    },
    'Admin': {
        'GET /admin-dashboard/': '/admin-dashboard/',
        'GET /api/admin/dashboard-stats/': '/api/admin/dashboard-stats/',
        'GET /admin-action-history/': '/admin-action-history/',
    },
    'Other Features': {
        'GET /find-my-car/': '/find-my-car/',
        'GET /search-by-phone/': '/search-by-phone/',
        'GET /parking-map/': '/parking-map/',
    }
}

print("\n" + "=" * 80)
print("COMPLETE ENDPOINT TEST & ERROR DETECTION")
print("=" * 80)

results = {}
errors_found = []

for category, urls in endpoints.items():
    results[category] = {'working': 0, 'failed': 0, 'errors': []}
    print(f"\n📍 {category}")
    print("-" * 80)
    
    for label, url in urls.items():
        try:
            response = client.get(url)
            
            # Check for errors in response
            is_error = response.status_code >= 500
            is_not_found = response.status_code == 404
            is_redirect = response.status_code == 302
            is_ok = response.status_code == 200
            
            if is_ok:
                results[category]['working'] += 1
                status = "✅"
                msg = f"{status} {label:40} [200 OK]"
            elif is_redirect:
                results[category]['working'] += 1
                status = "✅"
                msg = f"{status} {label:40} [302 REDIRECT - Requires Login]"
            elif is_not_found:
                results[category]['failed'] += 1
                status = "⚠️"
                msg = f"{status} {label:40} [404 NOT FOUND]"
                errors_found.append({'url': url, 'code': 404, 'message': 'Endpoint not found'})
                results[category]['errors'].append({'url': url, 'code': 404})
            else:
                results[category]['failed'] += 1
                status = "❌"
                msg = f"{status} {label:40} [{response.status_code} ERROR]"
                errors_found.append({'url': url, 'code': response.status_code, 'message': f'HTTP {response.status_code}'})
                results[category]['errors'].append({'url': url, 'code': response.status_code})
            
            print(msg)
            
            # Check for error content in response
            if is_error:
                if b'Traceback' in response.content or b'Error' in response.content:
                    print(f"     → Error Details in Response")
                    errors_found.append({'url': url, 'code': response.status_code, 'has_traceback': True})
        
        except Exception as e:
            results[category]['failed'] += 1
            msg = f"❌ {label:40} [EXCEPTION]"
            print(msg)
            print(f"     → {str(e)[:60]}")
            errors_found.append({'url': url, 'exception': str(e)})
            results[category]['errors'].append({'url': url, 'error': str(e)})

print("\n" + "=" * 80)
print("SUMMARY REPORT")
print("=" * 80)

total_working = sum(r['working'] for r in results.values())
total_failed = sum(r['failed'] for r in results.values())
total = total_working + total_failed

for category, result in results.items():
    if result['working'] + result['failed'] > 0:
        pct = (result['working'] / (result['working'] + result['failed']) * 100)
        status = "✅" if pct == 100 else "⚠️" if pct >= 80 else "❌"
        print(f"{status} {category:25} ✅ {result['working']:2} | ❌ {result['failed']:2} ({pct:.0f}%)")

print("\n" + "=" * 80)
print(f"OVERALL: {total_working}/{total} endpoints working ({total_working/total*100:.0f}%)")
print("=" * 80)

if errors_found:
    print(f"\n🔴 ERRORS FOUND: {len(errors_found)}")
    print("-" * 80)
    for i, error in enumerate(errors_found, 1):
        print(f"\n{i}. {error.get('url', 'Unknown')}")
        if 'code' in error:
            print(f"   Status Code: {error['code']}")
        if 'message' in error:
            print(f"   Issue: {error['message']}")
        if 'exception' in error:
            print(f"   Exception: {error['exception']}")
        if error.get('has_traceback'):
            print(f"   Type: Server Error (500)")
else:
    print("\n✅ NO CRITICAL ERRORS FOUND!")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print(f"""
1. ✅ = Working endpoints (200 OK or 302 Redirect)
2. ⚠️  = Not Found (404) - endpoint may not be defined
3. ❌ = Server Error (500+) - needs fixing
4. 302 Redirects are normal for login-protected pages

Next Steps:
- Any 500 errors need debugging in Django logs
- Any 404 errors mean URL patterns not defined
- Check Django shell for database issues
""")
