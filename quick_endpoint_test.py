#!/usr/bin/env python
"""Quick endpoint test"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')

import django
django.setup()

from django.test import Client

client = Client()
tests = [
    ('/heatmap/', 'Heatmap page'),
    ('/api/heatmap-realtime/1/', 'Real-time API'),
    ('/api/heatmap-analytics/1/', 'Analytics API'),
    ('/parking-history/', 'History page'),
    ('/my-reservations/', 'Reservations'),
    ('/notifications/', 'Notifications'),
    ('/api/parking-status/', 'Status API'),
    ('/api/parking-status/1/', 'Lot Status API'),
]

print("\nQUICK ENDPOINT TEST:\n" + "=" * 60)
working = 0
for url, name in tests:
    r = client.get(url)
    status = "✅" if r.status_code < 400 else ("⚠️" if r.status_code < 500 else "❌")
    code = r.status_code
    if r.status_code < 400:
        working += 1
    print(f"{status} {name:30} [{code}]")

print("=" * 60)
print(f"Result: {working}/{len(tests)} working\n")
