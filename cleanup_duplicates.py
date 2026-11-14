#!/usr/bin/env python
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkedVehicle, Vehicle
from django.utils import timezone

print("=" * 80)
print("PARKING DATA CLEANUP SCRIPT - SmartSlot Parking System")
print("=" * 80)

# Get all vehicles with multiple active parkings
vehicles_to_fix = {}
for vehicle in Vehicle.objects.all():
    active_parkings = ParkedVehicle.objects.filter(
        vehicle=vehicle, 
        checkout_time__isnull=True
    ).order_by('checkin_time')
    
    if active_parkings.count() > 1:
        vehicles_to_fix[vehicle.license_plate] = active_parkings

if not vehicles_to_fix:
    print("\n✅ No duplicate parkings found! Database is clean.")
    sys.exit(0)

print(f"\n⚠️  Found {len(vehicles_to_fix)} vehicles with duplicate active parkings")
print(f"Total duplicate records to clean: {sum(p.count()-1 for p in vehicles_to_fix.values())}\n")

# Option 1: Keep the most recent check-in, auto-checkout earlier ones
print("CLEANUP STRATEGY: Keep the most recent check-in, auto-checkout earlier duplicates")
print("-" * 80)

records_deleted = 0
records_archived = 0

for license_plate, parkings in sorted(vehicles_to_fix.items()):
    parkings_list = list(parkings.order_by('-checkin_time'))  # Most recent first
    keep_parking = parkings_list[0]  # Keep the most recent
    duplicate_parkings = parkings_list[1:]  # Remove the rest
    
    print(f"\n{license_plate}:")
    print(f"  → Keeping: {keep_parking.parking_lot.lot_name}, Spot {keep_parking.parking_spot.spot_number if keep_parking.parking_spot else 'N/A'}, {keep_parking.checkin_time}")
    
    for parking in duplicate_parkings:
        # OPTION A: Auto-checkout with calculated fee (safer approach)
        print(f"  → Auto-checkout: Lot {parking.parking_lot.lot_name}, Spot {parking.parking_spot.spot_number if parking.parking_spot else 'N/A'}, {parking.checkin_time}")
        
        # Calculate parking duration and fee
        duration_hours = (keep_parking.checkin_time - parking.checkin_time).total_seconds() / 3600
        fee = max(0, duration_hours * 50)  # ₹50/hour
        
        # Set checkout info
        parking.checkout_time = keep_parking.checkin_time  # Checkout when the other vehicle checked in
        parking.parking_duration = duration_hours
        parking.fee = fee
        parking.save()
        records_archived += 1

print(f"\n" + "=" * 80)
print(f"CLEANUP COMPLETE")
print(f"=" * 80)
print(f"✅ Auto-checked out {records_archived} duplicate parking records")
print(f"✅ All vehicles now have only one active parking session")

# Verification
print(f"\n[VERIFICATION]")
remaining_duplicates = 0
for vehicle in Vehicle.objects.all():
    active_count = ParkedVehicle.objects.filter(
        vehicle=vehicle,
        checkout_time__isnull=True
    ).count()
    if active_count > 1:
        remaining_duplicates += 1

if remaining_duplicates == 0:
    print("✅ Verification PASSED: No remaining duplicate parkings!")
else:
    print(f"⚠️  WARNING: {remaining_duplicates} vehicles still have duplicates!")

# Show updated statistics
total = ParkedVehicle.objects.count()
completed = ParkedVehicle.objects.filter(checkout_time__isnull=False).count()
active = ParkedVehicle.objects.filter(checkout_time__isnull=True).count()

print(f"\nUpdated Statistics:")
print(f"  Total Sessions: {total}")
print(f"  ✅ Completed: {completed} ({(completed/total*100):.1f}%)")
print(f"  🅿️  Active: {active} ({(active/total*100):.1f}%)")
