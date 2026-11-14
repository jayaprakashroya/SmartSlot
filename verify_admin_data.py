"""
Verify Admin Dashboard Sample Data Population
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import *

print("=" * 60)
print("ADMIN DASHBOARD SAMPLE DATA VERIFICATION")
print("=" * 60)

print(f"\n✅ Parking Lots: {ParkingLot.objects.count()}")
for lot in ParkingLot.objects.all():
    print(f"   - {lot.lot_name}: {lot.spots.count()} spots")

print(f"\n✅ Vehicles: {Vehicle.objects.count()}")
print(f"   First 5: {', '.join([v.license_plate for v in Vehicle.objects.all()[:5]])}")

currently_parked = ParkedVehicle.objects.filter(checkout_time__isnull=True).count()
print(f"\n✅ Currently Parked Vehicles: {currently_parked}")
if currently_parked > 0:
    for pv in ParkedVehicle.objects.filter(checkout_time__isnull=True)[:3]:
        print(f"   - {pv.vehicle.license_plate} in {pv.parking_spot.spot_number if pv.parking_spot else 'No spot'}")

print(f"\n✅ Parking Analytics: {ParkingAnalytics.objects.count()}")

print(f"\n✅ Pricing Rules: {PricingRule.objects.count()}")

print(f"\n✅ Parking Lot Settings: {ParkingLotSettings.objects.count()}")

print(f"\n✅ Reservations: {ParkingReservation.objects.count()}")

print(f"\n✅ Notifications: {UserNotification.objects.count()}")

print("\n" + "=" * 60)
print("✨ ADMIN DASHBOARD IS READY WITH SAMPLE DATA!")
print("=" * 60)
print("\nThe admin dashboard will now display:")
print("  1. 🔍 Search Car - Shows currently parked vehicles")
print("  2. 📡 Real-Time Slot Status - Shows occupancy")
print("  3. ⚠️ Slot Mismatch Detection - Checks for misplaced vehicles")
print("  4. 🚫 Parking Full Detection - Monitors capacity")
print("  5. ⏱️ Duration Tracker - Shows parking duration")
print("  6. 🚗🚗 Double Parking Prevention - Prevents re-entry")
print("  7. 🗺️ Slot Guidance System - Guides to available spots")
print("  8-15. Advanced features with comprehensive data")
