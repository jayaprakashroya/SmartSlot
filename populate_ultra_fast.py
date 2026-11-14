#!/usr/bin/env python
"""
Ultra-fast minimal data population using bulk operations
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from parkingapp.models import User_details, ParkingLot, ParkingSpot, Vehicle, ParkedVehicle

print("\n🚀 Ultra-Fast Data Population\n")

# Users (quick)
print("✓ Users...")
admin, _ = User.objects.get_or_create(username='admin'); admin.set_password('Admin@12345'); admin.save()
user, _ = User.objects.get_or_create(username='user'); user.set_password('User@12345'); user.save()
User_details.objects.get_or_create(Email='admin@smartslot.com', defaults={'Password': 'Admin@12345'})
User_details.objects.get_or_create(Email='user@smartslot.com', defaults={'Password': 'User@12345'})

# Lots (quick)
print("✓ Lots...")
lot1, _ = ParkingLot.objects.get_or_create(lot_name='Downtown Lot', defaults={'total_spots': 10})
lot2, _ = ParkingLot.objects.get_or_create(lot_name='Mall Lot', defaults={'total_spots': 10})

# Spots - use bulk_create for speed
print("✓ Spots (bulk insert)...")
spots_to_create = []
for lot in [lot1, lot2]:
    for i in range(1, 11):
        try:
            # Try to get first, but don't worry if it exists
            ParkingSpot.objects.get(parking_lot=lot, spot_number=f"{lot.lot_name[0]}{i:02d}")
        except ParkingSpot.DoesNotExist:
            spots_to_create.append(
                ParkingSpot(parking_lot=lot, spot_number=f"{lot.lot_name[0]}{i:02d}", spot_type='regular', x_position=i*100, y_position=i*50)
            )

if spots_to_create:
    ParkingSpot.objects.bulk_create(spots_to_create, ignore_conflicts=True)
    print(f"   Created {len(spots_to_create)} new spots")
else:
    print("   All spots already exist")

# Vehicles (quick)
print("✓ Vehicles...")
veh_data = [('ABC123', 'Owner1'), ('DEF456', 'Owner2'), ('GHI789', 'Owner3')]
for plate, owner in veh_data:
    Vehicle.objects.get_or_create(license_plate=plate, defaults={'vehicle_type': 'car', 'owner_name': owner, 'color': 'gray'})

# Parked vehicles (quick)
print("✓ Parked vehicles...")
spots = list(ParkingSpot.objects.all()[:3])
vehicles = list(Vehicle.objects.all()[:3])
parked_created = 0
for spot, vehicle in zip(spots, vehicles):
    try:
        existing = ParkedVehicle.objects.get(vehicle=vehicle, parking_spot=spot)
    except ParkedVehicle.DoesNotExist:
        ParkedVehicle.objects.create(
            vehicle=vehicle,
            parking_spot=spot,
            parking_lot=spot.parking_lot,
            checkin_time=datetime.now() - timedelta(hours=2),
            checkout_time=None,
            parking_fee=5.00
        )
        parked_created += 1

print("\n" + "="*60)
print("✅ DONE! Data is now in Neon")
print("="*60)
print(f"\n📊 Stats:")
print(f"  • User accounts: {User_details.objects.count()}")
print(f"  • Parking lots: {ParkingLot.objects.count()}")
print(f"  • Parking spots: {ParkingSpot.objects.count()}")
print(f"  • Vehicles: {Vehicle.objects.count()}")
print(f"  • Active parked vehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"\n🔐 Login: admin / Admin@12345")
print(f"🌐 www.smartslot-r2kq.onrender.com")
print(f"   Go to Heatmap page to see parking occupancy\n")
