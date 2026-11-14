#!/usr/bin/env python
"""
Ultra-simple Neon population - minimal queries
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from parkingapp.models import User_details, ParkingLot, ParkingSpot, Vehicle, ParkedVehicle

print("\n✓ Users...")
admin, _ = User.objects.get_or_create(username='admin'); admin.set_password('Admin@12345'); admin.save()
user, _ = User.objects.get_or_create(username='user'); user.set_password('User@12345'); user.save()
User_details.objects.get_or_create(Email='admin@smartslot.com', defaults={'Password': 'Admin@12345'})
User_details.objects.get_or_create(Email='user@smartslot.com', defaults={'Password': 'User@12345'})

print("✓ Lots...")
lot1, _ = ParkingLot.objects.get_or_create(lot_name='Downtown Lot', defaults={'total_spots': 10})

print("✓ Spots (batch)...")
spots_to_create = []
for i in range(1, 11):
    spots_to_create.append(
        ParkingSpot(parking_lot_id=lot1.lot_id, spot_number=f"D{i:02d}", spot_type='regular', x_position=i*100, y_position=i*50)
    )
ParkingSpot.objects.bulk_create(spots_to_create, ignore_conflicts=True)

print("✓ Vehicles...")
Vehicle.objects.get_or_create(license_plate='CAR001', defaults={'vehicle_type': 'car', 'owner_name': 'Owner1', 'color': 'gray'})
Vehicle.objects.get_or_create(license_plate='CAR002', defaults={'vehicle_type': 'car', 'owner_name': 'Owner2', 'color': 'gray'})

print("✓ Parked vehicles...")
# Fetch with select_related to avoid additional queries
spot = ParkingSpot.objects.select_related('parking_lot').filter(parking_lot_id=lot1.lot_id).first()
veh = Vehicle.objects.get(license_plate='CAR001')
if spot and veh:
    ParkedVehicle.objects.create(
        vehicle=veh,
        parking_spot=spot,
        parking_lot_id=lot1.lot_id,
        checkin_time=datetime.now() - timedelta(hours=2),
        parking_fee=5.00
    )

print("\n" + "="*50)
print("✅ Neon populated!")
print("="*50)
print(f"Users: {User_details.objects.count()}")
print(f"Lots: {ParkingLot.objects.count()}")
print(f"Spots: {ParkingSpot.objects.count()}")
print(f"Vehicles: {Vehicle.objects.count()}")
print(f"Parked: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"\nLogin: admin / Admin@12345")
print(f"URL: https://smartslot-r2kq.onrender.com\n")
