#!/usr/bin/env python
"""Create test parking data to verify heatmap colors"""

import os
import sys
import django
from random import randint

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle, Vehicle
from django.utils import timezone

def create_test_data():
    """Create test occupied/empty spots"""
    
    print("=" * 70)
    print("CREATING TEST DATA FOR HEATMAP")
    print("=" * 70)
    
    # Get or create parking lot
    lot, created = ParkingLot.objects.get_or_create(
        lot_id=1,
        defaults={
            'lot_name': 'Test Lot',
            'total_spots': 20,
            'location': 'Test Location'
        }
    )
    
    print(f"\n📍 Using Lot: {lot.lot_name} (Total: {lot.total_spots} spots)")
    
    # Clear existing parking records
    ParkedVehicle.objects.filter(parking_lot_id=lot.lot_id).delete()
    print("✓ Cleared existing parking records")
    
    # Get all spots in this lot
    spots = list(ParkingSpot.objects.filter(parking_lot=lot).order_by('spot_id')[:20])
    
    if not spots:
        print("❌ No parking spots found. Create spots first!")
        return
    
    print(f"✓ Found {len(spots)} spots")
    
    # Mark first 40% of spots as occupied
    occupied_count = max(1, len(spots) // 2)  # 50% occupancy
    
    print(f"\n🚗 Creating {occupied_count} occupied spots...")
    
    for i, spot in enumerate(spots[:occupied_count]):
        # Create vehicle
        plate = f"TEST_{i:03d}"
        vehicle, _ = Vehicle.objects.get_or_create(
            license_plate=plate,
            defaults={'vehicle_type': 'car', 'color': 'black'}
        )
        
        # Create parking record
        ParkedVehicle.objects.create(
            vehicle=vehicle,
            parking_spot=spot,
            parking_lot=lot,
            checkin_time=timezone.now(),
            detection_confidence=0.85
        )
        print(f"  ✓ Spot {spot.spot_number}: {plate}")
    
    print(f"\n✅ TEST DATA CREATED!")
    print(f"   Occupied spots: {occupied_count}")
    print(f"   Empty spots: {len(spots) - occupied_count}")
    print(f"   Occupancy: {round(occupied_count/len(spots)*100)}%")
    
    # Test heatmap
    from parkingapp.edge_case_handlers import HeatmapHandler
    
    print("\n🔄 Testing heatmap generation...")
    heatmap = HeatmapHandler.get_lot_heatmap(lot.lot_id)
    
    print(f"\n✅ HEATMAP COLORS:")
    green_count = sum(1 for s in heatmap['spots'] if s['color'] == 'green')
    red_count = sum(1 for s in heatmap['spots'] if s['color'] == 'red')
    
    print(f"  🟢 Green (Empty): {green_count}")
    print(f"  🔴 Red (Occupied): {red_count}")
    print(f"  Occupancy Rate: {heatmap['occupancy_rate']}%")
    
    if green_count == 0:
        print("\n⚠️  WARNING: No green spots! Check database...")
    if red_count == 0:
        print("\n⚠️  WARNING: No red spots! Check database...")

if __name__ == '__main__':
    create_test_data()
