#!/usr/bin/env python
"""
Fix parking spot colors - Reset and verify empty vs occupied status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle
from django.utils import timezone

print("=" * 70)
print("PARKING SPOT COLOR FIX - DIAGNOSTIC & RESET")
print("=" * 70)

# Step 1: Find all parking lots
print("\n[1] Checking parking lots...")
lots = ParkingLot.objects.all()
print(f"Found {lots.count()} parking lot(s)")

for lot in lots:
    print(f"\n  🅿️  Lot: {lot.lot_name}")
    print(f"      Total spots: {lot.total_spots}")
    
    # Get spots
    spots = lot.spots.all()
    print(f"      Spot objects in DB: {spots.count()}")
    
    # Check for active parking records
    active_parking = ParkedVehicle.objects.filter(
        parking_lot=lot,
        checkout_time__isnull=True
    )
    print(f"      Active vehicles: {active_parking.count()}")
    
    # Analyze each spot
    print(f"\n      Spot Status Analysis:")
    print(f"      {'Spot #':<10} {'Occupied':<12} {'Status':<20} {'Vehicle':<20}")
    print(f"      {'-'*62}")
    
    for spot in spots:
        is_occ = spot.is_occupied()
        status = "🔴 RED" if is_occ else "🟢 GREEN"
        vehicle = spot.get_current_vehicle()
        plate = vehicle.vehicle.license_plate if vehicle else "Empty"
        
        print(f"      {spot.spot_number:<10} {str(is_occ):<12} {status:<20} {plate:<20}")
    
    # Check for orphaned records
    print(f"\n      Checking for data issues:")
    
    # Records without checkout but spot says empty
    orphaned = 0
    for pv in ParkedVehicle.objects.filter(parking_lot=lot, checkout_time__isnull=True):
        if pv.parking_spot and pv.parking_spot not in spots:
            orphaned += 1
    
    if orphaned > 0:
        print(f"      ⚠️  {orphaned} parking records for spots not in this lot")
    
    # Count issue
    manual_count = ParkedVehicle.objects.filter(
        parking_lot=lot,
        checkout_time__isnull=True
    ).count()
    occupied_spots = sum(1 for s in spots if s.is_occupied())
    
    if manual_count != occupied_spots:
        print(f"      ⚠️  Mismatch: {manual_count} active records but {occupied_spots} occupied spots")
    else:
        print(f"      ✅ Consistency check passed")

# Step 2: Show what SHOULD happen
print("\n" + "=" * 70)
print("[2] Color Assignment Logic:")
print("=" * 70)
print("   If ParkedVehicle.objects.filter(")
print("       parking_spot=spot,")
print("       checkout_time__isnull=True  ← Active session")
print("   ).exists():")
print("       color = 'red'    🔴 OCCUPIED")
print("   else:")
print("       color = 'green'  🟢 EMPTY")

# Step 3: Fix recommendations
print("\n" + "=" * 70)
print("[3] Fix Recommendations:")
print("=" * 70)
print("\n✅ If ALL spots show as RED:")
print("   → Run: python fix_parking_colors.py --mark-all-empty")
print("   → This clears all active parking records")
print("   → Spots will show GREEN until vehicles are detected again")
print("\n✅ If specific spots show WRONG color:")
print("   → Check ParkedVehicle records for that spot")
print("   → Verify checkout_time is set correctly")
print("   → Run: python fix_parking_colors.py --verify")
print("\n✅ If YOLO isn't updating colors:")
print("   → Ensure YOLO is creating ParkedVehicle records")
print("   → Check yolov8_detector.py line 490+")
print("   → Run: python fix_parking_colors.py --sync-yolo")

print("\n" + "=" * 70)
