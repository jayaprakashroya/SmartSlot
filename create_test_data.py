#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import Vehicle, ParkingSpot, ParkedVehicle, ParkingLot
from django.utils import timezone

# Get or create a parking lot
lot, _ = ParkingLot.objects.get_or_create(
    lot_name="Default Lot",
    defaults={'total_spots': 100}
)

# Get or create a vehicle
vehicle, _ = Vehicle.objects.get_or_create(
    license_plate="KA01AB1234",
    defaults={
        'vehicle_type': 'car',
        'owner_name': 'Test Owner',
        'owner_phone': '9876543210'
    }
)

# Create parking spots if they don't exist
if ParkingSpot.objects.count() == 0:
    for i in range(1, 21):
        ParkingSpot.objects.create(lot=lot, spot_number=f"A{i:02d}", is_occupied=False)

# Get a parking spot
spot = ParkingSpot.objects.first()
spot.is_occupied = True
spot.save()

# Create parked vehicle record
parked = ParkedVehicle.objects.create(
    vehicle=vehicle,
    parking_spot=spot,
    parking_lot=lot
)

print(f"Created test data: Vehicle {vehicle.license_plate} at Spot {spot.spot_number}")
print(f"Total Vehicles: {Vehicle.objects.count()}")
print(f"Parked Vehicles: {ParkedVehicle.objects.count()}")
print(f"Parking Spots: {ParkingSpot.objects.count()}")
