#!/usr/bin/env python
"""
Update all parking lot locations to Puttaparthi, India
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLotSettings

# Puttaparthi locations
locations = {
    "Downtown Lot A": {
        "latitude": 13.8247,
        "longitude": 80.0644,
        "address": "Main Street, Puttaparthi, Andhra Pradesh 515134"
    },
    "Mall Lot B": {
        "latitude": 13.8350,
        "longitude": 80.0720,
        "address": "Shopping Complex, Puttaparthi, Andhra Pradesh 515134"
    },
    "Airport Lot C": {
        "latitude": 13.8150,
        "longitude": 80.0550,
        "address": "Terminal Parking, Puttaparthi, Andhra Pradesh 515134"
    },
    "Downtown Parking Garage": {
        "latitude": 13.8280,
        "longitude": 80.0670,
        "address": "Central Garage, Puttaparthi, Andhra Pradesh 515134"
    },
    "Shopping Mall Parking": {
        "latitude": 13.8380,
        "longitude": 80.0750,
        "address": "Mall Complex Basement, Puttaparthi, Andhra Pradesh 515134"
    },
    "Airport Terminal 1 Parking": {
        "latitude": 13.8120,
        "longitude": 80.0520,
        "address": "Terminal 1 Parking, Puttaparthi, Andhra Pradesh 515134"
    }
}

print("Updating parking lot locations to Puttaparthi...")
for settings in ParkingLotSettings.objects.all():
    lot_name = settings.parking_lot.lot_name
    if lot_name in locations:
        loc = locations[lot_name]
        settings.latitude = loc["latitude"]
        settings.longitude = loc["longitude"]
        settings.address = loc["address"]
        settings.phone = "+91-8555-000-000"  # Generic India phone
        settings.save()
        print(f"✓ Updated: {lot_name}")
    else:
        # Default to main Puttaparthi coordinates
        settings.latitude = 13.8247
        settings.longitude = 80.0644
        settings.address = "Puttaparthi, Andhra Pradesh 515134"
        settings.phone = "+91-8555-000-000"
        settings.save()
        print(f"✓ Updated (default): {lot_name}")

print("\n" + "="*60)
print("✓ ALL LOCATIONS UPDATED TO PUTTAPARTHI!")
print("="*60)
print(f"\nTotal locations updated: {ParkingLotSettings.objects.count()}")
print("Parking Map will now display Puttaparthi locations!")
print("="*60)
