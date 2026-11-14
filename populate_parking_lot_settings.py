#!/usr/bin/env python
"""
Populate ParkingLotSettings for all parking lots
This ensures the parking map displays correct location information
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot, ParkingLotSettings

# Sample parking lot locations (latitude, longitude) - Puttaparthi, India
locations = {
    "Downtown Lot A": {
        "latitude": 13.8247,
        "longitude": 80.0644,
        "address": "Main Street, Puttaparthi, Andhra Pradesh 515134",
        "phone": "+91-8555-123-456"
    },
    "Mall Lot B": {
        "latitude": 13.8350,
        "longitude": 80.0720,
        "address": "Shopping Complex, Puttaparthi, Andhra Pradesh 515134",
        "phone": "+91-8555-234-567"
    },
    "Airport Lot C": {
        "latitude": 13.8150,
        "longitude": 80.0550,
        "address": "Terminal Parking, Puttaparthi, Andhra Pradesh 515134",
        "phone": "+91-8555-345-678"
    }
}

print("Creating ParkingLotSettings...")
for lot in ParkingLot.objects.all():
    loc = locations.get(lot.lot_name, {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "address": f"{lot.lot_name} Location",
        "phone": "(555) 000-0000"
    })
    
    settings, created = ParkingLotSettings.objects.get_or_create(
        parking_lot=lot,
        defaults={
            "latitude": float(loc["latitude"]),
            "longitude": float(loc["longitude"]),
            "address": loc["address"],
            "phone": loc["phone"],
            "opening_time": "06:00",
            "closing_time": "23:00",
            "enable_reservations": True,
            "enable_dynamic_pricing": False,
            "enable_notifications": True,
            "gracePeriod_minutes": 15,
            "hourly_rate": Decimal("170.00")
        }
    )
    
    status = "created" if created else "already exists"
    print(f"✓ {lot.lot_name}: {status}")

print("\n" + "="*60)
print("✓ PARKING LOT SETTINGS CONFIGURED!")
print("="*60)
print(f"\nTotal lots configured: {ParkingLotSettings.objects.count()}")
print("\nParking Map is now ready to display!")
print("="*60)
