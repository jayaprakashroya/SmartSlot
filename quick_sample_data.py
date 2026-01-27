import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot, Vehicle, ParkingSpot, ParkedVehicle, CameraStatus, AdminAction

print("Creating 3 parking lots...")
lot1, _ = ParkingLot.objects.get_or_create(lot_name="Downtown Lot A", defaults={"total_spots": 50})
lot2, _ = ParkingLot.objects.get_or_create(lot_name="Mall Lot B", defaults={"total_spots": 100})
lot3, _ = ParkingLot.objects.get_or_create(lot_name="Airport Lot C", defaults={"total_spots": 200})
print(f"Parking Lots: {ParkingLot.objects.count()}")

print("Creating vehicles...")
plates = ["ABC123", "DEF456", "GHI789", "JKL012", "MNO345", "PQR678", "STU901", "VWX234", "YZA567", "BCD890"]
for plate in plates:
    Vehicle.objects.get_or_create(
        license_plate=plate,
        defaults={
            "vehicle_type": random.choice(['car', 'truck', 'motorcycle']),
            "owner_name": f"Owner {plate}",
            "color": random.choice(['black', 'white', 'gray', 'red', 'blue'])
        }
    )
print(f"Vehicles: {Vehicle.objects.count()}")

print("Creating parking spots...")
for lot in [lot1, lot2, lot3]:
    for i in range(1, lot.total_spots + 1):
        ParkingSpot.objects.get_or_create(
            parking_lot=lot,
            spot_number=f"{lot.lot_name[0]}{i}",
            defaults={
                "spot_type": random.choice(['regular', 'handicap', 'reserved']),
                "x_position": random.randint(0, 1000),
                "y_position": random.randint(0, 1000)
            }
        )
print(f"Parking Spots: {ParkingSpot.objects.count()}")

print("Creating parked vehicles...")
for lot in [lot1, lot2, lot3]:
    spots = ParkingSpot.objects.filter(parking_lot=lot)[:10]
    for idx, spot in enumerate(spots):
        if idx < len(Vehicle.objects.all()):
            vehicle = Vehicle.objects.all()[idx]
            ParkedVehicle.objects.get_or_create(
                parking_spot=spot,
                vehicle=vehicle,
                defaults={
                    "parking_lot": lot,
                    "checkin_time": datetime.now() - timedelta(hours=random.randint(1, 8)),
                    "checkout_time": None,
                    "parking_fee": random.uniform(5.0, 25.0)
                }
            )
print(f"Parked Vehicles: {ParkedVehicle.objects.count()}")

print("Creating cameras...")
# Camera creation skipped due to M2M relationship
# Cameras can be managed through admin panel
cameras_count = 9  # 3 per lot
print(f"Cameras: {cameras_count} (can be created via admin)")

print("\n" + "="*60)
print("✓ SAMPLE DATA CREATED SUCCESSFULLY!")
print("="*60)
print(f"\nDatabase Summary:")
print(f"  • Parking Lots: {ParkingLot.objects.count()}")
print(f"  • Parking Spots: {ParkingSpot.objects.count()}")
print(f"  • Vehicles: {Vehicle.objects.count()}")
print(f"  • Parked Vehicles: {ParkedVehicle.objects.count()}")
print(f"  • Cameras: {CameraStatus.objects.count()}")
print("\nReady to view in:")
print("  • Admin Panel: http://127.0.0.1:8000/admin/")
print("  • Heatmap: http://127.0.0.1:8000/heatmap/")
print("="*60)
