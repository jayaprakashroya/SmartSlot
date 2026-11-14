#!/usr/bin/env python
"""Diagnostic script to debug empty/occupied spot detection"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle
from django.utils import timezone

print("=" * 70)
print("EMPTY/OCCUPIED SPOT DIAGNOSTIC")
print("=" * 70)

# Get first lot
lot = ParkingLot.objects.first()
if not lot:
    print("❌ No parking lots in database")
    sys.exit(1)

print(f"\n📍 Lot: {lot.lot_name}")

# Get all spots
all_spots = list(ParkingSpot.objects.filter(parking_lot=lot))
print(f"📊 Total spots in lot: {len(all_spots)}")

# Check each spot
print("\n🔍 SPOT STATUS CHECK:")
print("-" * 70)

occupied_via_method = 0
empty_via_method = 0
occupied_via_query = set()

for spot in all_spots[:10]:
    # Method 1: Using is_occupied() method
    is_occ_method = spot.is_occupied()
    
    # Method 2: Direct query
    has_active = ParkedVehicle.objects.filter(
        parking_spot=spot,
        checkout_time__isnull=True
    ).exists()
    
    # Get active vehicle if any
    active_vehicle = ParkedVehicle.objects.filter(
        parking_spot=spot,
        checkout_time__isnull=True
    ).first()
    
    status = "OCCUPIED" if is_occ_method else "EMPTY"
    plate = active_vehicle.vehicle.license_plate if active_vehicle else "N/A"
    
    print(f"Spot {spot.spot_number:<5} | {status:<10} | {plate:<20} | Method: {is_occ_method} | Query: {has_active}")
    
    if is_occ_method:
        occupied_via_method += 1
        occupied_via_query.add(spot.spot_id)
    else:
        empty_via_method += 1

print("-" * 70)
print(f"\n✅ Summary:")
print(f"  Occupied (via method): {occupied_via_method}")
print(f"  Empty (via method): {empty_via_method}")
print(f"  Occupied (via direct query): {len(occupied_via_query)}")

# Check database directly
all_active = ParkedVehicle.objects.filter(
    parking_lot=lot,
    checkout_time__isnull=True
)

print(f"\n🗄️  Database Status:")
print(f"  Total active ParkedVehicle records: {all_active.count()}")

if all_active.exists():
    print(f"  Active records:")
    for record in all_active[:5]:
        print(f"    - Spot {record.parking_spot.spot_number}: {record.vehicle.license_plate}")

# Test heatmap colors
print(f"\n🎨 Testing Heatmap:")
from parkingapp.edge_case_handlers import HeatmapHandler

try:
    heatmap = HeatmapHandler.get_lot_heatmap(lot.lot_id)
    
    green_spots = [s for s in heatmap['spots'] if s['color'] == 'green']
    red_spots = [s for s in heatmap['spots'] if s['color'] == 'red']
    
    print(f"  Green (empty): {len(green_spots)}")
    print(f"  Red (occupied): {len(red_spots)}")
    print(f"  Occupancy: {heatmap['occupancy_rate']}%")
    
    if len(green_spots) == 0:
        print("\n⚠️  WARNING: ALL SPOTS SHOWING AS RED/OCCUPIED!")
        print("     This suggests is_occupied() is returning True for all spots")
    elif len(red_spots) == 0:
        print("\n⚠️  WARNING: ALL SPOTS SHOWING AS GREEN/EMPTY!")
        print("     This suggests is_occupied() is returning False for all spots")
    else:
        print("\n✅ Heatmap working correctly!")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
