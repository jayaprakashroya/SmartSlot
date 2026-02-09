#!/usr/bin/env python
"""
Populate edge-case & professional sample data for dashboards
- PendingSyncQueue entries (simulated offline syncs)
- DetectionLog entries (low confidence & normal)
- DisputeLog entries (pending + resolved)
- AdminAction logs (force_release + manual actions)
- ParkingAnalytics entries for heatmap/demo
- ParkingSession entries to support Payments/History

Run with Django settings loaded (DATABASE_URL should point to Neon for production)
"""
import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import (
    PendingSyncQueue, DetectionLog, DisputeLog, AdminAction,
    ParkingAnalytics, ParkingLot, ParkingSpot, Vehicle, ParkedVehicle,
    User_details, ParkingSession, Payment
)
from django.utils import timezone

print("\n== Edge-case sample data population starting ==")

# Ensure at least one lot exists
lot = ParkingLot.objects.first()
if not lot:
    lot = ParkingLot.objects.create(lot_name='EdgeCase Lot', total_spots=20)
    print(f"Created lot: {lot.lot_name}")
else:
    print(f"Using lot: {lot.lot_name}")

# 1) Pending syncs (simulate 2 failed sync entries)
print('\n-- PendingSyncQueue --')
for i in range(2):
    frame_id = f'frame_{i}'
    # avoid duplicate pending syncs for same frame
    exists = PendingSyncQueue.objects.filter(data__frame_id=frame_id).exists()
    if not exists:
        q = PendingSyncQueue.objects.create(
            record_type='vehicle_entry',
            vehicle_id=None,
            parking_spot_id=None,
            data={'reason': 'offline_capture', 'frame_id': frame_id, 'info': 'simulated'},
            synced=False
        )
        print(f"  Created pending sync id: {q.sync_id}")
    else:
        q = PendingSyncQueue.objects.filter(data__frame_id=frame_id).first()
        print(f"  Pending sync already exists id: {q.sync_id}")

# 2) Detection logs (one low confidence, one normal)
print('\n-- DetectionLog --')
cam = None
try:
    cam = lot.cameras.first()
except Exception:
    cam = None

low = DetectionLog.objects.create(
    camera=cam,
    vehicles_detected=2,
    confidence_scores=[0.4, 0.35],
    license_plates=['XYZ123', 'UNK000'],
    plate_confidence=[0.4, 0.3],
    frame_image='detection_frames/sample_low.jpg',
    manual_override=False
)
print(f"  Low-confidence detection id: {low.detection_id}")

hi = DetectionLog.objects.create(
    camera=cam,
    vehicles_detected=3,
    confidence_scores=[0.95, 0.9, 0.88],
    license_plates=['ABC123', 'DEF456', 'GHI789'],
    plate_confidence=[0.95, 0.9, 0.88],
    frame_image='detection_frames/sample_good.jpg',
    manual_override=False
)
print(f"  Good detection id: {hi.detection_id}")

# 3) Dispute logs (pending and resolved)
print('\n-- DisputeLog --')
# Find or create a parked vehicle to attach dispute
vehicle = Vehicle.objects.first()
parked = ParkedVehicle.objects.filter(checkout_time__isnull=True).first()
if not vehicle:
    vehicle = Vehicle.objects.create(license_plate='DISP01', vehicle_type='car')
if not parked:
    # create a parked vehicle record
    spot = ParkingSpot.objects.filter(parking_lot=lot).first()
    if not spot:
        spot = ParkingSpot.objects.create(parking_lot=lot, spot_number='EC01', x_position=10, y_position=10)
    parked = ParkedVehicle.objects.create(vehicle=vehicle, parking_spot=spot, parking_lot=lot, checkin_time=timezone.now()-timedelta(hours=2))

d1 = DisputeLog.objects.create(
    parked_vehicle=parked,
    customer_name='Alice',
    customer_phone='+10000000001',
    dispute_type='car_not_found',
    description='Customer says car not at spot',
    status='pending'
)
print(f"  Dispute pending id: {d1.dispute_id}")

d2 = DisputeLog.objects.create(
    parked_vehicle=parked,
    customer_name='Bob',
    customer_phone='+10000000002',
    dispute_type='wrong_spot',
    description='Wrong spot assigned',
    status='resolved_refund',
    admin_notes='Refund issued',
    refund_amount=10.00
)
print(f"  Dispute resolved id: {d2.dispute_id}")

# 4) AdminAction logs
print('\n-- AdminAction --')
a1 = AdminAction.objects.create(
    admin_name='sysadmin',
    action_type='force_release',
    parking_spot=parked.parking_spot,
    vehicle=parked.vehicle,
    reason='Manual release during maintenance',
    before_state={'occupied': True},
    after_state={'occupied': False}
)
print(f"  Admin action id: {a1.action_id}")

# 5) ParkingAnalytics entries
print('\n-- ParkingAnalytics --')
analytics_date = (timezone.now()-timedelta(days=1)).date()
# upsert analytics to avoid unique constraint errors
analytics, created = ParkingAnalytics.objects.update_or_create(
    parking_lot=lot,
    date=analytics_date,
    defaults={
        'total_sessions': 50,
        'peak_occupancy_percent': 85,
        'average_duration_minutes': 75,
        'total_revenue': 1250.00,
        'peak_hour': 18
    }
)
if created:
    print(f"  Analytics id: {analytics.analytics_id} (created)")
else:
    print(f"  Analytics id: {analytics.analytics_id} (updated)")

# 6) ParkingSessions + Payments to show payments/history
print('\n-- ParkingSession & Payment --')
user = User_details.objects.first()
if not user:
    user = User_details.objects.create(Email='edgeuser@example.com', Password='edgepass')
sess_defaults = {
    'user': user,
    'parking_lot': lot,
    'parking_spot': parked.parking_spot,
    'license_plate': parked.vehicle.license_plate,
    'exit_time': timezone.now()-timedelta(hours=1),
    'duration_minutes': 120,
    'parking_fee': 10.00,
    'payment_status': 'paid'
}
entry_time = timezone.now()-timedelta(hours=3)
sess, created_sess = ParkingSession.objects.get_or_create(
    license_plate=parked.vehicle.license_plate,
    entry_time=entry_time,
    defaults=sess_defaults
)
if created_sess:
    print(f"  ParkingSession id: {sess.session_id} (created)")
else:
    print(f"  ParkingSession id: {sess.session_id} (existing)")

# If Payment model has 'user' or 'user_email', try to create a sample payment
p_fields = [f.name for f in Payment._meta.get_fields()]
payment_kwargs = {
    'parking_session': sess,
    'amount': sess.parking_fee,
    'payment_method': 'mock',
    'payment_status': 'completed',
    'transaction_id': f"EDGE-TXN-{int(timezone.now().timestamp())}"
}
if 'user' in p_fields:
    payment_kwargs['user'] = user
elif 'user_email' in p_fields:
    payment_kwargs['user_email'] = user.Email

try:
    # try to avoid duplicate payments for same transaction_id
    txn = payment_kwargs.get('transaction_id')
    if txn and Payment.objects.filter(transaction_id=txn).exists():
        pay = Payment.objects.get(transaction_id=txn)
        print(f"  Payment exists: {getattr(pay, 'payment_id', getattr(pay, 'id', 'n/a'))}")
    else:
        pay = Payment.objects.create(**payment_kwargs)
        print(f"  Payment id created: {getattr(pay, 'payment_id', getattr(pay, 'id', 'n/a'))}")
except Exception as e:
    print(f"  Could not create payment: {e}")

print('\n== Edge-case sample data population complete ==')

# Summary counts
print(f"\nSummary:")
print(f"  PendingSyncQueue: {PendingSyncQueue.objects.filter(synced=False).count()}")
print(f"  DetectionLog: {DetectionLog.objects.count()}")
print(f"  DisputeLog pending: {DisputeLog.objects.filter(status='pending').count()}")
print(f"  AdminAction: {AdminAction.objects.count()}")
print(f"  ParkingAnalytics: {ParkingAnalytics.objects.count()}")
print(f"  Active ParkedVehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"  ParkingSessions: {ParkingSession.objects.count()}")
print(f"  Payments: {Payment.objects.count()}")
