import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
import django
django.setup()
from django.utils import timezone
from parkingapp.models import (
    PendingSyncQueue, DetectionLog, DisputeLog, AdminAction,
    ParkingAnalytics, ParkingSession, Payment, ParkedVehicle, ParkingLot
)

print("\n== Edge-case DB Verification ==")
print(f"PendingSyncQueue (unsynced): {PendingSyncQueue.objects.filter(synced=False).count()}")
print(f"DetectionLog (total): {DetectionLog.objects.count()}")
print(f"DisputeLog pending: {DisputeLog.objects.filter(status='pending').count()}")
print(f"DisputeLog resolved: {DisputeLog.objects.exclude(status='pending').count()}")
print(f"AdminAction: {AdminAction.objects.count()}")
print(f"ParkingAnalytics entries: {ParkingAnalytics.objects.count()}")
print(f"Active ParkedVehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"ParkingSessions: {ParkingSession.objects.count()}")
print(f"Payments: {Payment.objects.count()}")

# Basic heatmap occupancy (latest analytics peak_occupancy_percent if exists)
pa = ParkingAnalytics.objects.order_by('-date').first()
if pa:
    print(f"Latest analytics: lot_id={pa.parking_lot_id} date={pa.date} peak_occupancy_percent={pa.peak_occupancy_percent}")
else:
    print("Latest analytics: none")

# List lots and current active occupancy percent by counting parked vehicles per lot
print('\nLot occupancy:')
for lot in ParkingLot.objects.all():
    total_spots = getattr(lot, 'total_spots', 0) or 0
    active = ParkedVehicle.objects.filter(parking_lot=lot, checkout_time__isnull=True).count()
    pct = (active / total_spots * 100) if total_spots else 0
    print(f"  {lot.lot_name} (id={lot.lot_id}): {active}/{total_spots} -> {pct:.1f}%")

print('\n== End verification ==\n')