import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, Vehicle, ParkedVehicle

print("Creating minimal parking data (1 lot, 30 spots, 5 parked vehicles)...")

lot, _ = ParkingLot.objects.get_or_create(lot_name="Demo Lot Minimal", defaults={"total_spots": 30})

# Create 30 spots
for i in range(1, 31):
    spot_number = f"D{i}"
    ParkingSpot.objects.get_or_create(
        parking_lot=lot,
        spot_number=spot_number,
        defaults={
            "spot_type": "regular",
            "x_position": i * 10,
            "y_position": i * 5
        }
    )

print(f"Parking Spots now: {ParkingSpot.objects.filter(parking_lot=lot).count()}")

# Create vehicles
plates = ["MIN1", "MIN2", "MIN3", "MIN4", "MIN5"]
for plate in plates:
    Vehicle.objects.get_or_create(
        license_plate=plate,
        defaults={
            "vehicle_type": "car",
            "owner_name": f"Owner {plate}",
            "color": "gray"
        }
    )

# Park first 5 spots
spots = ParkingSpot.objects.filter(parking_lot=lot).order_by('spot_id')[:5]
for idx, spot in enumerate(spots):
    vehicle = Vehicle.objects.get(license_plate=plates[idx])
    ParkedVehicle.objects.get_or_create(
        vehicle=vehicle,
        parking_spot=spot,
        defaults={
            "parking_lot": lot,
            "checkin_time": datetime.now() - timedelta(hours=(idx+1)),
            "checkout_time": None,
            "parking_fee": 0
        }
    )

print("Done.")
print(f"ParkingLot count: {ParkingLot.objects.count()}")
print(f"ParkingSpot count: {ParkingSpot.objects.count()}")
print(f"Vehicles count: {Vehicle.objects.count()}")
print(f"Active parked vehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
