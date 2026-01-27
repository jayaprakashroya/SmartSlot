#!/usr/bin/env python
"""Test to diagnose why empty spots are marking as red"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle
from parkingapp.parking_manager import ParkingManager

lot = ParkingLot.objects.first()
if not lot:
    print("❌ No parking lots in database. Creating test data...")
    lot = ParkingLot.objects.create(lot_name="Test Lot", total_spots=10)
    for i in range(1, 11):
        ParkingSpot.objects.create(
            parking_lot=lot,
            spot_number=f"A{i}",
            x_position=100 + i*50,
            y_position=100
        )
    print("✅ Test data created")

print(f"\n📍 Lot: {lot.lot_name}")
print(f"   Total Spots: {lot.total_spots}")

status = ParkingManager.get_parking_lot_status(lot)
if status:
    print(f"\n📊 Status Report:")
    print(f"   Occupied: {status['occupied_spots']}")
    print(f"   Available: {status['available_spots']}")
    print(f"   Occupancy: {status['occupancy_rate']}%")
    
    print(f"\n🔍 Spot Details:")
    for spot in status['spots']:
        css_class = "occupied (RED)" if spot['is_occupied'] else "available (GREEN)"
        vehicle = spot['vehicle_plate'] if spot['is_occupied'] else "Empty"
        print(f"   {spot['spot_number']:3} - {css_class:20} - Vehicle: {vehicle}")
else:
    print("❌ Error getting parking lot status")
