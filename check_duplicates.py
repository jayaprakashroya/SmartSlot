#!/usr/bin/env python
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkedVehicle, Vehicle
from django.db.models import Count

print("=" * 80)
print("DATABASE INTEGRITY CHECK - SmartSlot Parking System")
print("=" * 80)

# Check 1: Total records
print(f"\n[1] TOTAL RECORDS")
print(f"    Total ParkedVehicle records: {ParkedVehicle.objects.count()}")
print(f"    Total Vehicle records: {Vehicle.objects.count()}")

# Check 2: Vehicles with multiple simultaneous parkings
print(f"\n[2] DUPLICATE PARKING CHECK - Vehicles parked at multiple locations")
print("    (Same vehicle with multiple checkout_time=NULL records)")
print("-" * 80)

duplicates = {}
for vehicle in Vehicle.objects.all():
    active_parkings = ParkedVehicle.objects.filter(
        vehicle=vehicle, 
        checkout_time__isnull=True
    ).count()
    
    if active_parkings > 1:
        duplicates[vehicle.license_plate] = active_parkings

if duplicates:
    print(f"⚠️  FOUND {len(duplicates)} VEHICLES WITH MULTIPLE ACTIVE PARKINGS:\n")
    for plate, count in sorted(duplicates.items()):
        print(f"    {plate}: {count} simultaneous parkings")
        parkings = ParkedVehicle.objects.filter(
            vehicle__license_plate=plate,
            checkout_time__isnull=True
        )
        for parking in parkings:
            print(f"        - Lot: {parking.parking_lot.lot_name}, Spot: {parking.parking_spot.spot_number if parking.parking_spot else 'N/A'}, Checkin: {parking.checkin_time}")
else:
    print("✅ NO DUPLICATE ACTIVE PARKINGS FOUND")

# Check 3: Vehicle history analysis
print(f"\n[3] VEHICLE HISTORY ANALYSIS")
print("-" * 80)

vehicles_with_history = Vehicle.objects.all().order_by('-vehicle_id')[:5]

print(f"Sample Vehicles:")
for vehicle in vehicles_with_history:
    total_sessions = ParkedVehicle.objects.filter(vehicle=vehicle).count()
    completed_sessions = ParkedVehicle.objects.filter(vehicle=vehicle, checkout_time__isnull=False).count()
    active_sessions = ParkedVehicle.objects.filter(vehicle=vehicle, checkout_time__isnull=True).count()
    print(f"    {vehicle.license_plate}: {total_sessions} total | {completed_sessions} completed | {active_sessions} active")

# Check 4: Parking Session Status
print(f"\n[4] PARKING SESSION STATUS BREAKDOWN")
print("-" * 80)

total = ParkedVehicle.objects.count()
completed = ParkedVehicle.objects.filter(checkout_time__isnull=False).count()
active = ParkedVehicle.objects.filter(checkout_time__isnull=True).count()

print(f"    Total Sessions: {total}")
print(f"    ✅ Completed (with checkout): {completed} ({(completed/total*100):.1f}%)")
print(f"    🅿️  Active (no checkout): {active} ({(active/total*100):.1f}%)")

# Check 5: Database file info
print(f"\n[5] DATABASE FILE")
print("-" * 80)

import subprocess
result = subprocess.run(
    ['powershell', '-Command', 'Get-Item "c:\\Users\\maner\\Downloads\\SmartSlot\\myenv\\Smart-car-parking\\db.sqlite3" | Select-Object Length, LastWriteTime'],
    capture_output=True,
    text=True
)
print(result.stdout)

print("\n" + "=" * 80)
print("Check complete!")
print("=" * 80)
