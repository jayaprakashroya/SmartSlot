#!/usr/bin/env python
"""
Fast minimal data population for Neon
- 2 lots (15 spots each)
- 6 vehicles
- 4 parked vehicles
"""
import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from parkingapp.models import User_details, ParkingLot, ParkingSpot, Vehicle, ParkedVehicle

print("\n🚀 Fast Minimal Data Population\n")

# Users
print("1️⃣ Users...")
admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@smartslot.com', 'is_staff': True, 'is_superuser': True})
admin_user.set_password('Admin@12345')
admin_user.save()

user, _ = User.objects.get_or_create(username='user', defaults={'email': 'user@smartslot.com'})
user.set_password('User@12345')
user.save()

User_details.objects.get_or_create(Email='admin@smartslot.com', defaults={'Password': 'Admin@12345'})
User_details.objects.get_or_create(Email='user@smartslot.com', defaults={'Password': 'User@12345'})
print(f"   ✓ {User_details.objects.count()} users\n")

# Lots
print("2️⃣ Parking lots...")
lot1, c1 = ParkingLot.objects.get_or_create(lot_name='Downtown Lot', defaults={'total_spots': 15})
lot2, c2 = ParkingLot.objects.get_or_create(lot_name='Mall Lot', defaults={'total_spots': 15})
print(f"   ✓ {ParkingLot.objects.count()} lots\n")

# Spots - batch insert for speed
print("3️⃣ Parking spots (this may take 30-60 seconds)...")
for lot in [lot1, lot2]:
    for i in range(1, 16):
        ParkingSpot.objects.get_or_create(
            parking_lot=lot,
            spot_number=f"{lot.lot_name[0]}{i:02d}",
            defaults={'spot_type': 'regular', 'x_position': i*100, 'y_position': i*50}
        )
print(f"   ✓ {ParkingSpot.objects.count()} spots\n")

# Vehicles
print("4️⃣ Vehicles...")
for plate in ['ABC123', 'DEF456', 'GHI789', 'JKL012', 'MNO345', 'PQR678']:
    Vehicle.objects.get_or_create(license_plate=plate, defaults={'vehicle_type': 'car', 'owner_name': f'Owner {plate}', 'color': 'gray'})
print(f"   ✓ {Vehicle.objects.count()} vehicles\n")

# Parked vehicles
print("5️⃣ Parked vehicles...")
spots = list(ParkingSpot.objects.all()[:4])
vehicles = list(Vehicle.objects.all()[:4])
for spot, vehicle in zip(spots, vehicles):
    ParkedVehicle.objects.get_or_create(
        vehicle=vehicle,
        parking_spot=spot,
        defaults={'parking_lot': spot.parking_lot, 'checkin_time': datetime.now() - timedelta(hours=2), 'checkout_time': None, 'parking_fee': 5.00}
    )
print(f"   ✓ {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()} parked\n")

print("="*60)
print("✅ DATA POPULATION COMPLETE")
print("="*60)
print(f"\n📊 Summary:")
print(f"  • Users: {User_details.objects.count()}")
print(f"  • Parking lots: {ParkingLot.objects.count()}")
print(f"  • Parking spots: {ParkingSpot.objects.count()}")
print(f"  • Vehicles: {Vehicle.objects.count()}")
print(f"  • Active parked vehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"\n🔐 Login: admin / Admin@12345  OR  user / User@12345")
print(f"🌐 https://smartslot-r2kq.onrender.com")
print(f"   Heatmap should now show {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}/30 occupancy\n")
