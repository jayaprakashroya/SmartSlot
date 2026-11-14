import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'ParkingProject.settings'

import django
django.setup()

from django.test import Client

print("Testing Heatmap Feature Buttons...\n")
c = Client()

buttons = {
    'Parking History': '/parking-history/',
    'Reservations': '/my-reservations/', 
    'Notifications': '/notifications/',
    'Real-Time Status': '/parking-lot-status/',
}

for name, url in buttons.items():
    resp = c.get(url)
    status = "PASS" if resp.status_code == 200 else f"FAIL ({resp.status_code})"
    print(f"{name:20} {url:25} {status}")

print("\nAll buttons tested!")
