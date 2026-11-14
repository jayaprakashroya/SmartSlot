#!/usr/bin/env python
"""
Fix: Duplicate/Simultaneous Parking Records

Problem: Same vehicle (ABC123) is parked at multiple locations at the same time
Root Cause: Populate script cycles through vehicles without checking if they're already active
Solution: 
  1. Add database constraint to prevent simultaneous parking
  2. Clean up duplicate records (keep only one active per vehicle)
  3. Fix populate script to not create duplicates
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkedVehicle, Vehicle
from django.db.models import Q
from datetime import datetime

print("=" * 80)
print("FIXING DUPLICATE SIMULTANEOUS PARKING RECORDS")
print("=" * 80)

# Step 1: Find all vehicles with multiple active parking sessions
print("\n📊 AUDIT: Vehicles with Multiple Active Parking Sessions")
print("-" * 80)

vehicles_with_duplicates = {}
all_vehicles = Vehicle.objects.all()

for vehicle in all_vehicles:
    # Find all active parking sessions for this vehicle
    active_sessions = ParkedVehicle.objects.filter(
        vehicle=vehicle,
        checkout_time__isnull=True  # Still parked
    )
    
    if active_sessions.count() > 1:
        vehicles_with_duplicates[vehicle.license_plate] = active_sessions.count()
        print(f"⚠️  {vehicle.license_plate}: {active_sessions.count()} active sessions")
        
        # Show details
        for session in active_sessions:
            print(f"   ├─ {session.parking_lot.lot_name} - Spot {session.parking_spot.spot_number if session.parking_spot else 'N/A'}")
            print(f"   │  Entry: {session.checkin_time}")
            print(f"   │  Fee: ₹{session.parking_fee}")

if not vehicles_with_duplicates:
    print("✅ No vehicles with multiple active sessions found!")
else:
    print(f"\n❌ Found {len(vehicles_with_duplicates)} vehicles with duplicates")

# Step 2: Clean up duplicates by keeping newest, deleting others
print("\n🧹 CLEANUP: Removing Duplicate Records")
print("-" * 80)

total_deleted = 0

for vehicle in Vehicle.objects.filter(parking_history__checkout_time__isnull=True).distinct():
    active_sessions = ParkedVehicle.objects.filter(
        vehicle=vehicle,
        checkout_time__isnull=True
    ).order_by('-checkin_time')  # Most recent first
    
    if active_sessions.count() > 1:
        # Keep the most recent one, delete others
        keep_record = active_sessions.first()
        delete_records = active_sessions[1:]
        
        deleted_count = 0
        for record in delete_records:
            print(f"  🗑️  Deleting {vehicle.license_plate} from {record.parking_lot.lot_name}")
            record.delete()
            deleted_count += 1
            total_deleted += 1
        
        print(f"  ✓ Kept: {vehicle.license_plate} at {keep_record.parking_lot.lot_name}")

print(f"\n✅ Deleted {total_deleted} duplicate records")

# Step 3: Verify cleanup
print("\n✔️  VERIFICATION: Checking Results")
print("-" * 80)

# Re-check for any remaining duplicates
remaining_duplicates = 0
for vehicle in Vehicle.objects.all():
    active_count = ParkedVehicle.objects.filter(
        vehicle=vehicle,
        checkout_time__isnull=True
    ).count()
    
    if active_count > 1:
        print(f"⚠️  {vehicle.license_plate}: Still has {active_count} active sessions")
        remaining_duplicates += 1

if remaining_duplicates == 0:
    print("✅ All vehicles have at most 1 active parking session")
else:
    print(f"❌ Still found {remaining_duplicates} vehicles with duplicates")

# Step 4: Display healthy records now
print("\n📋 HEALTHY RECORDS: Active Parking Sessions (After Cleanup)")
print("-" * 80)

active_records = ParkedVehicle.objects.filter(checkout_time__isnull=True).order_by('-checkin_time')[:20]

if active_records.count() == 0:
    print("No active parking sessions")
else:
    print(f"{'Vehicle':<10} {'Lot':<25} {'Spot':<6} {'Entry Time':<20} {'Duration':<12} {'Fee':<10}")
    print("-" * 90)
    
    for record in active_records:
        duration = "Active"
        if record.duration_minutes:
            duration = f"{record.duration_minutes} min"
        
        print(f"{record.vehicle.license_plate:<10} {record.parking_lot.lot_name:<25} {record.parking_spot.spot_number if record.parking_spot else 'N/A':<6} {str(record.checkin_time):<20} {duration:<12} ₹{record.parking_fee:<9}")

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
