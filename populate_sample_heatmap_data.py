import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import (
    ParkingLot, Vehicle, ParkingSpot, ParkedVehicle, 
    Contact_Message, AdminAction, CameraStatus
)

print("=" * 75)
print("POPULATING SMARTSLOT WITH SAMPLE DATA")
print("=" * 75)

# Clear existing data
print("\nClearing existing data...")
ParkingLot.objects.all().delete()
Vehicle.objects.all().delete()
ParkingSpot.objects.all().delete()
ParkedVehicle.objects.all().delete()
AdminAction.objects.all().delete()
CameraStatus.objects.all().delete()

# Create Parking Lots
print("\n✓ Creating Parking Lots...")
parking_lots = []

lot1 = ParkingLot.objects.create(
    lot_name="Downtown Parking Lot A",
    total_spots=50
)
parking_lots.append(lot1)

lot2 = ParkingLot.objects.create(
    lot_name="Mall Parking Level B1",
    total_spots=100
)
parking_lots.append(lot2)

lot3 = ParkingLot.objects.create(
    lot_name="Airport Short-Term Parking",
    total_spots=200
)
parking_lots.append(lot3)

print(f"✓ Created {len(parking_lots)} parking lots")

# Create Vehicles
print("\n✓ Creating Sample Vehicles...")
vehicles = []
license_plates = [
    "ABC123", "XYZ789", "DEF456", "GHI789", "JKL012",
    "MNO345", "PQR678", "STU901", "VWX234", "YZA567",
    "BCD890", "EFG123", "HIJ456", "KLM789", "NOP012"
]

for plate in license_plates:
    vehicle = Vehicle.objects.create(
        license_plate=plate,
        vehicle_type=random.choice(['car', 'truck', 'motorcycle']),
        color=random.choice(['black', 'white', 'gray', 'red', 'blue', 'silver']),
        owner_name=f"Owner_{plate}",
        owner_phone="1234567890"
    )
    vehicles.append(vehicle)

print(f"✓ Created {len(vehicles)} vehicles")

# Create Parking Spots for each lot
print("\n✓ Creating Parking Spots...")
spots_created = 0

for lot in parking_lots:
    for spot_num in range(1, lot.total_spots + 1):
        spot = ParkingSpot.objects.create(
            parking_lot=lot,
            spot_number=f"SPOT-{lot.lot_id}-{spot_num}",
            spot_type=random.choice(['regular', 'handicap', 'reserved']),
            x_position=random.randint(0, 1000),
            y_position=random.randint(0, 1000)
        )
        spots_created += 1

print(f"✓ Created {spots_created} parking spots")

# Create Parked Vehicles
print("\n✓ Creating Parked Vehicle Records...")
parked_count = 0

for lot in parking_lots:
    occupied_spots = ParkingSpot.objects.filter(lot=lot, is_occupied=True)
    for idx, spot in enumerate(occupied_spots):
        if idx < len(vehicles):
            parked = ParkedVehicle.objects.create(
                lot=lot,
                spot=spot,
                vehicle=vehicles[idx],
                entry_time=datetime.now() - timedelta(hours=random.randint(1, 8)),
                exit_time=None,
                is_parked=True,
                parking_fee=random.uniform(5.0, 25.0)
            )
            parked_count += 1

print(f"✓ Created {parked_count} parked vehicle records")

# Create Admin Actions for audit trail
print("\n✓ Creating Admin Actions...")
actions_created = 0

actions_data = [
    "Verified parking lot layout",
    "Updated camera configurations",
    "Generated parking report",
    "Processed refund request",
    "Resolved parking dispute",
    "Updated pricing structure",
    "Maintenance check completed",
    "System diagnostics run"
]

for i in range(20):
    action = AdminAction.objects.create(
        action_type=random.choice(actions_data),
        description=f"Admin action #{i+1}: {random.choice(actions_data)}",
        timestamp=datetime.now() - timedelta(hours=random.randint(0, 48)),
        affected_lot=random.choice(parking_lots) if random.random() > 0.3 else None
    )
    actions_created += 1

print(f"✓ Created {actions_created} admin actions")

# Create Camera Status records
print("\n✓ Creating Camera Status Records...")
camera_count = 0

for lot in parking_lots:
    for cam_num in range(1, random.randint(3, 6)):
        camera = CameraStatus.objects.create(
            lot=lot,
            camera_id=f"CAM_{lot.id}_{cam_num}",
            is_active=random.choice([True, True, True, False]),  # 75% active
            last_checked=datetime.now() - timedelta(minutes=random.randint(1, 60)),
            resolution="1080p",
            frame_rate=30
        )
        camera_count += 1

print(f"✓ Created {camera_count} camera status records")

# Create sample heatmap data
print("\n✓ Creating Heatmap Data...")

heatmap_data = [
    {"time_period": "08:00-09:00", "occupancy": 85},
    {"time_period": "09:00-10:00", "occupancy": 78},
    {"time_period": "10:00-11:00", "occupancy": 72},
    {"time_period": "11:00-12:00", "occupancy": 68},
    {"time_period": "12:00-13:00", "occupancy": 95},
    {"time_period": "13:00-14:00", "occupancy": 92},
    {"time_period": "14:00-15:00", "occupancy": 88},
    {"time_period": "15:00-16:00", "occupancy": 82},
    {"time_period": "16:00-17:00", "occupancy": 75},
    {"time_period": "17:00-18:00", "occupancy": 70},
    {"time_period": "18:00-19:00", "occupancy": 65},
]

print(f"✓ Heatmap data prepared for {len(heatmap_data)} time periods")

# Print Summary
print("\n" + "=" * 75)
print("✓ SAMPLE DATA SUCCESSFULLY POPULATED")
print("=" * 75)

print(f"\n📊 DATA SUMMARY:")
print(f"  • Parking Lots: {ParkingLot.objects.count()}")
print(f"  • Total Spots: {ParkingSpot.objects.count()}")
print(f"  • Vehicles: {Vehicle.objects.count()}")
print(f"  • Parked Vehicles: {ParkedVehicle.objects.count()}")
print(f"  • Admin Actions: {AdminAction.objects.count()}")
print(f"  • Cameras: {CameraStatus.objects.count()}")

print(f"\n🎯 PARKING LOT DETAILS:")
for lot in ParkingLot.objects.all():
    occupied = ParkingSpot.objects.filter(lot=lot, is_occupied=True).count()
    total = ParkingSpot.objects.filter(lot=lot).count()
    available = total - occupied
    occupancy_rate = (occupied / total * 100) if total > 0 else 0
    
    print(f"\n  📍 {lot.lot_name}")
    print(f"     • Total Spots: {total}")
    print(f"     • Occupied: {occupied}")
    print(f"     • Available: {available}")
    print(f"     • Occupancy Rate: {occupancy_rate:.1f}%")
    print(f"     • Cameras: {CameraStatus.objects.filter(lot=lot).count()}")

print(f"\n🔥 HEATMAP DATA - PEAK HOURS:")
for data in heatmap_data:
    occupancy = data["occupancy"]
    bar = "█" * (occupancy // 5)
    print(f"  {data['time_period']}: {bar} {occupancy}%")

print(f"\n" + "=" * 75)
print("✓ Ready to view in Admin Dashboard & Heatmap!")
print("  • Admin Panel: http://127.0.0.1:8000/admin/")
print("  • Heatmap: http://127.0.0.1:8000/heatmap/")
print("=" * 75)
