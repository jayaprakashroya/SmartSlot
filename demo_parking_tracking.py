"""
SmartSlot Parking Spot Tracking System - Demo Script
Demonstrates how to use the parking management system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, Vehicle, ParkedVehicle
from parkingapp.parking_manager import ParkingManager
from datetime import timedelta
from django.utils import timezone

print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║         SmartSlot Parking System - Demo & Test Script          ║
║                                                                ║
║    Testing Car-to-Parking-Spot Tracking System                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")


def demo_1_setup_parking_lot():
    """Demo 1: Create a parking lot with spots"""
    print("\n[DEMO 1] Setting Up Parking Lot")
    print("=" * 60)
    
    # Create or get parking lot
    lot, created = ParkingLot.objects.get_or_create(
        lot_name="Downtown Parking - Level 1",
        defaults={'total_spots': 20}
    )
    
    if created:
        print(f"✅ Created parking lot: {lot.lot_name}")
        
        # Create parking spots
        print("Creating 20 parking spots...")
        for i in range(1, 21):
            row = chr(64 + (i // 10) + 1)  # A, B, C
            number = i % 10 if i % 10 != 0 else 10
            spot_number = f"{row}{number}"
            
            ParkingSpot.objects.get_or_create(
                parking_lot=lot,
                spot_number=spot_number,
                defaults={
                    'spot_type': 'vip' if i <= 2 else 'reserved' if i <= 4 else 'regular',
                    'x_position': 107 * ((i - 1) % 5),
                    'y_position': 48 * ((i - 1) // 5),
                    'spot_width': 107,
                    'spot_height': 48
                }
            )
        
        print(f"✅ Created 20 parking spots")
    else:
        print(f"ℹ️  Parking lot already exists: {lot.lot_name}")
    
    return lot


def demo_2_vehicle_checkin():
    """Demo 2: Check in vehicles"""
    print("\n[DEMO 2] Vehicle Check-In")
    print("=" * 60)
    
    lot = ParkingLot.objects.get(lot_name="Downtown Parking - Level 1")
    
    vehicles = [
        ("ABC 1234", "John Doe", "+1-555-0001", "Red"),
        ("XYZ 5678", "Jane Smith", "+1-555-0002", "Blue"),
        ("DEF 9012", "Bob Johnson", "+1-555-0003", "Black"),
        ("GHI 3456", "Alice Williams", "+1-555-0004", "White"),
    ]
    
    for license_plate, owner, phone, color in vehicles:
        parked = ParkingManager.checkin_vehicle(
            license_plate=license_plate,
            parking_lot=lot,
            vehicle_type='car',
            owner_name=owner,
            owner_phone=phone,
            color=color
        )
        
        if parked:
            spot = parked.parking_spot
            print(f"✅ {license_plate} ({owner}) → Spot {spot.spot_number} ({spot.get_spot_type_display()})")


def demo_3_find_vehicle():
    """Demo 3: Find vehicle by license plate"""
    print("\n[DEMO 3] Find Vehicle Location")
    print("=" * 60)
    
    search_plates = ["ABC 1234", "XYZ 5678", "INVALID"]
    
    for plate in search_plates:
        result = ParkingManager.find_vehicle_location(plate)
        
        if result:
            print(f"\n✅ Found: {result['license_plate']}")
            print(f"   Owner: {result['owner_name']}")
            print(f"   Location: {result['parking_lot']} - Spot {result['spot_number']}")
            print(f"   Type: {result['spot_type']}")
            print(f"   Parked since: {result['checkin_time'].strftime('%H:%M:%S')}")
            print(f"   Duration: {result['duration']}")
        else:
            print(f"❌ Not found: {plate}")


def demo_4_parking_lot_status():
    """Demo 4: Get parking lot status"""
    print("\n[DEMO 4] Parking Lot Status")
    print("=" * 60)
    
    lot = ParkingLot.objects.get(lot_name="Downtown Parking - Level 1")
    status = ParkingManager.get_parking_lot_status(lot)
    
    print(f"\n📍 {status['lot_name']}")
    print(f"   Total Spots: {status['total_spots']}")
    print(f"   Occupied: {status['occupied_spots']}")
    print(f"   Available: {status['available_spots']}")
    print(f"   Occupancy: {status['occupancy_rate']}%")
    
    print("\n   Spot Details:")
    occupied_count = 0
    for spot in status['spots']:
        if spot['is_occupied']:
            occupied_count += 1
            print(f"   🔴 {spot['spot_number']:3} - {spot['vehicle_plate']} ({spot['spot_type']})")
    
    print(f"\n   {status['available_spots']} spots available")


def demo_5_vehicle_checkout():
    """Demo 5: Check out vehicle"""
    print("\n[DEMO 5] Vehicle Check-Out")
    print("=" * 60)
    
    checkout_plate = "ABC 1234"
    
    parked = ParkingManager.checkout_vehicle(checkout_plate)
    
    if parked:
        print(f"✅ {checkout_plate} checked out")
        print(f"   From Spot: {parked.parking_spot.spot_number}")
        print(f"   Duration: {parked.get_duration_display()}")
        print(f"   Checked out at: {parked.checkout_time.strftime('%H:%M:%S')}")
        print(f"   Status: {parked.payment_status}")


def demo_6_vehicle_history():
    """Demo 6: View vehicle history"""
    print("\n[DEMO 6] Vehicle Parking History")
    print("=" * 60)
    
    lot = ParkingLot.objects.get(lot_name="Downtown Parking - Level 1")
    activity = ParkingManager.get_recent_activity(lot, hours=24)
    
    print(f"\nRecent parking activity (last 24 hours):\n")
    for record in activity:
        status = "✅ Checked Out" if record.checkout_time else "🟢 Still Parked"
        print(f"   {record.vehicle.license_plate:12} | {record.parking_spot.spot_number:3} | {record.get_duration_display():10} | {status}")


def demo_7_statistics():
    """Demo 7: Get parking statistics"""
    print("\n[DEMO 7] Parking Statistics")
    print("=" * 60)
    
    lot = ParkingLot.objects.get(lot_name="Downtown Parking - Level 1")
    stats = ParkingManager.get_parking_statistics(lot, days=7)
    
    print(f"\nStatistics (Last {stats['period_days']} days):")
    print(f"   Unique Vehicles: {stats['total_unique_vehicles']}")
    print(f"   Total Sessions: {stats['total_parking_sessions']}")
    print(f"   Average Duration: {stats['average_duration_hours']:.2f} hours")


def demo_8_api_examples():
    """Demo 8: API usage examples"""
    print("\n[DEMO 8] API Endpoint Examples")
    print("=" * 60)
    
    print("""
These endpoints are now available on your Django server:

📍 Customer Facing Pages:
   • GET /find-my-car
     Enter license plate to find parking spot
   
   • GET /parking-lot-status
     View all spots and occupancy status
   
   • GET /vehicle-history
     View parking history for a vehicle

🔌 API Endpoints (JSON responses):
   • GET /api/find-vehicle/?plate=ABC1234
     Find vehicle location by license plate
   
   • GET /api/parking-status/
     Get current parking lot status
   
   • GET /api/parking-statistics/7/
     Get statistics for last 7 days
   
   • GET /api/recent-activity/24/
     Get activity for last 24 hours

Examples:
   curl "http://localhost:8000/api/find-vehicle/?plate=ABC1234"
   curl "http://localhost:8000/api/parking-status/"
   curl "http://localhost:8000/api/parking-statistics/7/"
    """)


def main():
    """Run all demos"""
    try:
        print("\n🔄 Cleaning up previous demo data...")
        ParkedVehicle.objects.all().delete()
        ParkingSpot.objects.all().delete()
        ParkingLot.objects.all().delete()
        Vehicle.objects.all().delete()
        print("✅ Cleanup complete\n")
        
        demo_1_setup_parking_lot()
        demo_2_vehicle_checkin()
        demo_3_find_vehicle()
        demo_4_parking_lot_status()
        demo_5_vehicle_checkout()
        demo_6_vehicle_history()
        demo_7_statistics()
        demo_8_api_examples()
        
        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        print("""
Next steps:
1. Start the Django server: python manage.py runserver
2. Visit http://localhost:8000/find-my-car to test customer interface
3. Visit http://localhost:8000/admin to manage parking system
4. Use the API endpoints to integrate with other systems
        """)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
