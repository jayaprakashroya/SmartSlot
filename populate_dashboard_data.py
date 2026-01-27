"""
Populate sample data for all dashboard buttons to work
Run: python manage.py shell < populate_dashboard_data.py
"""

import os
import django
from django.utils import timezone
from datetime import timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import (
    ParkingLot, ParkingSpot, Vehicle, ParkedVehicle, 
    DetectionLog, DisputeLog, AdminAction, CameraStatus, ParkingHistory
)

def clear_existing_data():
    """Clear all existing data"""
    print("Clearing existing data...")
    ParkingHistory.objects.all().delete()
    DisputeLog.objects.all().delete()
    AdminAction.objects.all().delete()
    DetectionLog.objects.all().delete()
    ParkedVehicle.objects.all().delete()
    Vehicle.objects.all().delete()
    ParkingSpot.objects.all().delete()
    CameraStatus.objects.all().delete()
    ParkingLot.objects.all().delete()
    print("✓ Data cleared")

def create_parking_lots():
    """Create parking lots"""
    print("\n📍 Creating parking lots...")
    lots = []
    
    lot_names = ['Main Parking', 'North Wing', 'South Wing', 'Basement Level 1', 'Basement Level 2']
    for name in lot_names:
        lot = ParkingLot.objects.create(
            lot_name=name,
            total_spots=50
        )
        lots.append(lot)
        print(f"  ✓ Created: {name}")
    
    return lots

def create_parking_spots(lots):
    """Create parking spots for each lot"""
    print("\n🅿️ Creating parking spots...")
    
    all_spots = []
    spot_types = ['regular', 'reserved', 'handicap', 'vip']
    
    for lot in lots:
        for i in range(1, 51):
            spot_type = random.choice(spot_types)
            spot = ParkingSpot.objects.create(
                parking_lot=lot,
                spot_number=f"{lot.lot_name[0:3].upper()}-{i:03d}",
                spot_type=spot_type,
                x_position=random.randint(100, 1200),
                y_position=random.randint(50, 700),
            )
            all_spots.append(spot)
    
    print(f"  ✓ Created {len(all_spots)} parking spots")
    return all_spots

def create_vehicles(count=30):
    """Create vehicles"""
    print(f"\n🚗 Creating {count} vehicles...")
    
    plate_prefixes = ['ABC', 'XYZ', 'PQR', 'LMN', 'EFG']
    vehicles = []
    
    for i in range(count):
        plate = f"{random.choice(plate_prefixes)}-{random.randint(1000, 9999)}"
        vehicle = Vehicle.objects.create(
            license_plate=plate,
            vehicle_type=random.choice(['car', 'truck', 'motorcycle', 'bus']),
            owner_name=f"Owner-{random.randint(100, 999)}",
            owner_phone=f"555-{random.randint(1000, 9999)}",
            color=random.choice(['red', 'blue', 'white', 'black', 'silver']),
        )
        vehicles.append(vehicle)
    
    print(f"  ✓ Created {count} vehicles")
    return vehicles

def create_parked_vehicles(vehicles, spots):
    """Create parked vehicle records"""
    print("\n🅿️ Creating parked vehicle records...")
    
    parked_count = min(25, len(vehicles))  # Park 25 vehicles
    lots = list(ParkingLot.objects.all())
    
    for i in range(parked_count):
        vehicle = vehicles[i]
        spot = spots[i]
        lot = lots[i % len(lots)] if lots else spot.parking_lot
        
        # Create parking entry
        parked = ParkedVehicle.objects.create(
            vehicle=vehicle,
            parking_spot=spot,
            parking_lot=lot,
            checkin_time=timezone.now() - timedelta(hours=random.randint(1, 12)),
            checkout_time=None,  # Still parked
        )
        
        print(f"  ✓ {vehicle.license_plate} → {spot.spot_number}")
    
    # Create some checkout records for history
    print("\n📋 Creating parking history...")
    for i in range(parked_count, parked_count + 10):
        if i < len(vehicles):
            vehicle = vehicles[i]
            spot = spots[i] if i < len(spots) else spots[0]
            lot = lots[i % len(lots)] if lots else spot.parking_lot
            
            checkin_time = timezone.now() - timedelta(hours=random.randint(2, 24))
            checkout_time = checkin_time + timedelta(hours=random.randint(1, 8))
            
            parked = ParkedVehicle.objects.create(
                vehicle=vehicle,
                parking_spot=spot,
                parking_lot=lot,
                checkin_time=checkin_time,
                checkout_time=checkout_time,
            )
            
            # Create parking history
            ParkingHistory.objects.create(
                phone_number=f"555-{random.randint(1000, 9999)}",
                parked_vehicle=parked,
                ticket_id=f"TKT-{parked.parking_record_id:05d}" if parked.parking_record_id else f"TKT-{random.randint(10000, 99999)}"
            )
            
            print(f"  ✓ History: {vehicle.license_plate}")

def create_detection_logs(count=15):
    """Create detection logs"""
    print(f"\n📸 Creating {count} detection logs...")
    
    for i in range(count):
        DetectionLog.objects.create(
            vehicles_detected=random.randint(1, 5),
            confidence_scores=[random.uniform(0.7, 0.99) for _ in range(random.randint(1, 5))],
            license_plates=[f"ABC-{random.randint(1000, 9999)}" for _ in range(random.randint(1, 3))],
            plate_confidence=[random.uniform(0.75, 0.99) for _ in range(random.randint(1, 3))],
            manual_override=random.choice([True, False]),
        )
    
    print(f"  ✓ Created {count} detection logs")

def create_disputes():
    """Create dispute records"""
    print("\n⚖️ Creating dispute records...")
    
    parked_vehicles = ParkedVehicle.objects.all()[:5]
    dispute_types = ['car_not_found', 'wrong_spot', 'damage', 'double_charge', 'other']
    
    for pv in parked_vehicles:
        dispute = DisputeLog.objects.create(
            parked_vehicle=pv,
            customer_name=f"Customer-{random.randint(100, 999)}",
            customer_phone=f"555-{random.randint(1000, 9999)}",
            dispute_type=random.choice(dispute_types),
            description="Sample dispute for testing dashboard",
            detection_confidence=random.uniform(0.85, 0.99),
            status=random.choice(['pending', 'investigating', 'resolved_refund', 'resolved_valid']),
        )
        print(f"  ✓ Dispute: {dispute.dispute_type}")

def create_admin_actions():
    """Create admin action logs"""
    print("\n👨‍💼 Creating admin actions...")
    
    spots = ParkingSpot.objects.all()[:5]
    vehicles = Vehicle.objects.all()[:5]
    action_types = ['force_release', 'manual_entry', 'manual_exit', 'override_detection']
    
    for i in range(5):
        AdminAction.objects.create(
            admin_name=f"Admin-User-{i+1}",
            action_type=random.choice(action_types),
            parking_spot=spots[i % len(spots)],
            vehicle=vehicles[i % len(vehicles)],
            reason="Sample admin action for testing",
            notes=f"Action #{i+1}",
        )
        print(f"  ✓ Admin action created")

def create_camera_status(lots):
    """Create camera status records"""
    print("\n📹 Creating camera status records...")
    
    for lot in lots:
        camera = CameraStatus.objects.create(
            camera_name=f"{lot.lot_name} - Camera 1",
            parking_lot=lot,
            status=random.choice(['online', 'online', 'online', 'offline']),  # 75% online
            last_seen=timezone.now() if random.random() > 0.2 else timezone.now() - timedelta(hours=2),
        )
        
        # Assign some spots to camera
        spots = lot.spots.all()[:10]
        for spot in spots:
            camera.spot_coverage.add(spot)
        
        print(f"  ✓ Camera: {camera.camera_name}")

def main():
    print("\n" + "="*60)
    print("🚀 POPULATING DASHBOARD DATA")
    print("="*60)
    
    try:
        # Clear existing data
        clear_existing_data()
        
        # Create all data
        lots = create_parking_lots()
        spots = create_parking_spots(lots)
        vehicles = create_vehicles(count=35)
        create_parked_vehicles(vehicles, spots)
        create_detection_logs(count=20)
        create_disputes()
        create_admin_actions()
        create_camera_status(lots)
        
        print("\n" + "="*60)
        print("✅ DATA POPULATION COMPLETE!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"  • Parking Lots: {ParkingLot.objects.count()}")
        print(f"  • Parking Spots: {ParkingSpot.objects.count()}")
        print(f"  • Vehicles: {Vehicle.objects.count()}")
        print(f"  • Currently Parked: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
        print(f"  • Parking History: {ParkingHistory.objects.count()}")
        print(f"  • Detection Logs: {DetectionLog.objects.count()}")
        print(f"  • Disputes: {DisputeLog.objects.count()}")
        print(f"  • Admin Actions: {AdminAction.objects.count()}")
        print(f"  • Cameras: {CameraStatus.objects.count()}")
        print("\n✨ All dashboard buttons should now work!")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
