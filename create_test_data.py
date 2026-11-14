#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import Vehicle, ParkingSpot, ParkedVehicle, ParkingLot
from django.utils import timezone

# A small helper to create a vehicle and optionally a parked record
import random

def make_vehicle(lot_prefix, index):
    # deterministic plate so each parked record is identifiable
    plate = f"{lot_prefix}{index:03d}"
    vehicle, _ = Vehicle.objects.get_or_create(
        license_plate=plate,
        defaults={
            'vehicle_type': 'car',
            'owner_name': f'{lot_prefix} Owner',
            'owner_phone': '9999999999'
        }
    )
    return vehicle

# lots we want to seed along with how many occupied spots to simulate
# third element is number of occupied slots; prefix used for plates
lots_data = [
    ('Airport Terminal A', 200, 50, 'ATA'),
    ('Downtown Plaza', 120, 30, 'DTP'),
    ('EdgeCase Lot', 20, 1, 'ECL'),
    ('Hospital Emergency', 80, 10, 'HSP'),
    ('Office Building Central', 100, 20, 'OBC'),
    ('Shopping Mall West', 150, 25, 'SMW'),
]

for lot_name, total_spots, occupied_count, prefix in lots_data:
    lot, created = ParkingLot.objects.get_or_create(
        lot_name=lot_name,
        defaults={'total_spots': total_spots}
    )
    if not created and lot.total_spots != total_spots:
        lot.total_spots = total_spots
        lot.save()

    # ensure parking spots exist for this lot
    existing_spots = ParkingSpot.objects.filter(lot=lot).count()
    if existing_spots < total_spots:
        for i in range(existing_spots + 1, total_spots + 1):
            ParkingSpot.objects.create(lot=lot, spot_number=f"P{i:03d}", is_occupied=False)

    # make some spots occupied with parked vehicles
    # first clear any active records for this lot
    ParkedVehicle.objects.filter(parking_lot=lot, checkout_time__isnull=True).delete()
    spots = list(ParkingSpot.objects.filter(lot=lot))
    random.shuffle(spots)

    for idx, spot in enumerate(spots[:occupied_count], start=1):
        spot.is_occupied = True
        spot.save()
        # create vehicle using lot-specific prefix
        vehicle = make_vehicle(prefix, idx)
        ParkedVehicle.objects.create(
            vehicle=vehicle,
            parking_spot=spot,
            parking_lot=lot
        )
        print(f"    parked {vehicle.license_plate} at spot {spot.spot_number}")

    # make sure remaining spots are free
    for spot in spots[occupied_count:]:
        spot.is_occupied = False
        spot.save()

    print(f"Seeded lot '{lot_name}' with {occupied_count} occupied of {total_spots} spots")

print(f"Total Vehicles: {Vehicle.objects.count()}")
print(f"Parked Vehicles (active): {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"Parking Spots: {ParkingSpot.objects.count()}")
