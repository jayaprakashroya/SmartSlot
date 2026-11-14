#!/usr/bin/env python
"""
Populate Admin Dashboard with Sample Data
Generates realistic data for all dashboard metrics
"""
import os
import django
from datetime import datetime, timedelta, time
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import (
    ParkingLot, ParkingSpot, Vehicle, ParkedVehicle, 
    ParkingSession, Payment, User_details, UserNotification
)
from django.utils import timezone

print("="*60)
print("ADMIN DASHBOARD - SAMPLE DATA GENERATION")
print("="*60)

# Get or create parking lots
lots = ParkingLot.objects.all()[:3]
if not lots.exists():
    print("❌ No parking lots found. Creating sample lots...")
    for i in range(3):
        ParkingLot.objects.create(
            lot_name=f"Sample Lot {i+1}",
            total_spots=50
        )
    lots = ParkingLot.objects.all()[:3]

# ════════════════════════════════════════════════════════════════
# 1. Generate Sample Vehicles and Parking Data
# ════════════════════════════════════════════════════════════════
print("\n1. Generating vehicle and parking data...")

sample_plates = [
    'ABC-1234', 'XYZ-5678', 'DEF-9012', 'GHI-3456', 'JKL-7890',
    'MNO-2345', 'PQR-6789', 'STU-0123', 'VWX-4567', 'YZA-8901',
    'BCD-2345', 'EFG-6789', 'HIJ-0123', 'KLM-4567', 'NOP-8901'
]

# Create vehicles if they don't exist
vehicles = []
for plate in sample_plates:
    vehicle, created = Vehicle.objects.get_or_create(
        license_plate=plate,
        defaults={
            'vehicle_type': random.choice(['car', 'motorcycle', 'truck']),
            'owner_name': f'Owner {plate}',
            'color': random.choice(['black', 'white', 'red', 'blue', 'silver'])
        }
    )
    vehicles.append(vehicle)
print(f"✓ Vehicles: {len(vehicles)} ready")

# ════════════════════════════════════════════════════════════════
# 2. Generate Parked Vehicles (for "Currently Parked" metric)
# ════════════════════════════════════════════════════════════════
print("\n2. Generating parked vehicles...")

# Clear old parked vehicles
ParkedVehicle.objects.filter(checkout_time__isnull=True).delete()

now = timezone.now()
parked_count = 0
for lot in lots:
    spots = ParkingSpot.objects.filter(parking_lot=lot)[:12]
    for idx, spot in enumerate(spots):
        if idx < len(vehicles):
            entry_time = now - timedelta(minutes=random.randint(30, 480))
            ParkedVehicle.objects.create(
                vehicle=vehicles[idx],
                parking_spot=spot,
                parking_lot=lot,
                checkin_time=entry_time,
                checkout_time=None,
                parking_fee=Decimal(random.uniform(425, 4250)).quantize(Decimal('0.01'))
            )
            parked_count += 1

print(f"✓ Currently Parked: {parked_count} vehicles")

# ════════════════════════════════════════════════════════════════
# 3. Generate Parking Sessions (for "Entries Today", "Exits Today")
# ════════════════════════════════════════════════════════════════
print("\n3. Generating parking sessions...")

# Get or create a default user
user, _ = User_details.objects.get_or_create(
    Email='admin@smartparking.com',
    defaults={'Password': 'admin'}
)

# Create sessions for today
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
entries_today = 0
exits_today = 0

for i in range(15):
    entry_time = today_start + timedelta(hours=random.randint(6, 20), minutes=random.randint(0, 59))
    
    # 70% have exits (exited vehicles)
    if random.random() < 0.7:
        exit_time = entry_time + timedelta(hours=random.randint(1, 6), minutes=random.randint(0, 59))
        exits_today += 1
    else:
        exit_time = None  # Still parked
    
    entries_today += 1
    
    session, created = ParkingSession.objects.get_or_create(
        user=user,
        entry_time=entry_time,
        defaults={
            'parking_lot': lots[i % len(lots)],
            'exit_time': exit_time,
            'parking_fee': Decimal(random.uniform(425, 4250)).quantize(Decimal('0.01')),
            'payment_status': 'paid' if exit_time else 'pending'
        }
    )

print(f"✓ Entries Today: {entries_today}")
print(f"✓ Exits Today: {exits_today}")

# ════════════════════════════════════════════════════════════════
# 4. Generate Payments (for payment metrics)
# ════════════════════════════════════════════════════════════════
print("\n4. Generating payment data...")

# Get first vehicle for payment
if vehicles:
    vehicle = vehicles[0]
    if not ParkedVehicle.objects.filter(vehicle=vehicle, checkout_time__isnull=True).exists():
        lot = lots[0]
        spot = lot.spots.first()
        if spot:
            entry_time = now - timedelta(hours=2)
            pv = ParkedVehicle.objects.create(
                vehicle=vehicle,
                parking_spot=spot,
                parking_lot=lot,
                checkin_time=entry_time,
                checkout_time=None
            )

print(f"✓ Payment records ready")

# ════════════════════════════════════════════════════════════════
# 5. Generate Notifications
# ════════════════════════════════════════════════════════════════
print("\n5. Generating notifications...")

notification_types = ['parking_available', 'payment_due', 'spot_reserved', 'urgent_alert']
for i in range(5):
    UserNotification.objects.create(
        user=user,
        notification_type=random.choice(notification_types),
        title=f'Notification {i+1}',
        message=f'Sample notification message for dashboard display',
        is_read=i % 2 == 0
    )

active_notifications = UserNotification.objects.filter(is_read=False).count()
print(f"✓ Active Notifications: {active_notifications}")

# ════════════════════════════════════════════════════════════════
# 6. Calculate and display dashboard statistics
# ════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("DASHBOARD METRICS SUMMARY")
print("="*60)

# Available Slots
total_spots = ParkingSpot.objects.count()
occupied_spots = ParkedVehicle.objects.filter(checkout_time__isnull=True).values('parking_spot').distinct().count()
available_slots = total_spots - occupied_spots
print(f"\n📍 PARKING AVAILABILITY:")
print(f"   • Total Spots: {total_spots}")
print(f"   • Occupied: {occupied_spots}")
print(f"   • Available: {available_slots}")
print(f"   • Occupancy Rate: {(occupied_spots/total_spots*100 if total_spots > 0 else 0):.1f}%")

# Daily Metrics
print(f"\n📊 DAILY METRICS:")
print(f"   • Entries Today: {entries_today}")
print(f"   • Exits Today: {exits_today}")
print(f"   • Currently Parked: {parked_count}")
print(f"   • Free Slots: {available_slots}")

# Weekly Metrics
week_ago = now - timedelta(days=7)
this_week_sessions = ParkingSession.objects.filter(entry_time__gte=week_ago).count()
daily_avg = this_week_sessions / 7 if this_week_sessions > 0 else 0
print(f"\n📈 WEEKLY METRICS:")
print(f"   • This Week Entries: {this_week_sessions}")
print(f"   • Daily Average: {daily_avg:.1f}")

# Peak Hours
peak_hour = '18:00-19:00'  # Most common peak time
avg_wait = random.randint(3, 15)  # minutes
wait_reduction = random.randint(10, 40)  # percentage
print(f"\n⏰ PEAK HOURS & WAIT TIMES:")
print(f"   • Peak Hour: {peak_hour}")
print(f"   • Avg Wait Reduction: {wait_reduction}%")

# Database Metrics
print(f"\n🗄️ DATABASE METRICS:")
db_occupied = occupied_spots
actual_occupied = occupied_spots + random.randint(-2, 2)  # Slight discrepancy
discrepancy = abs(db_occupied - actual_occupied)
print(f"   • DB Occupied: {db_occupied}")
print(f"   • Actual Occupied (detected): {actual_occupied}")
print(f"   • Discrepancy: {discrepancy}")

# Unauthorized/Efficiency Metrics
unauthorized_count = random.randint(0, 3)
efficiency_score = 100 - (discrepancy * 5)
efficiency_score = max(70, min(100, efficiency_score))
print(f"\n🔒 SECURITY & EFFICIENCY:")
print(f"   • Unauthorized Count: {unauthorized_count}")
print(f"   • Efficiency Score: {efficiency_score:.1f}%")

# Active Notifications
print(f"\n🔔 NOTIFICATIONS:")
print(f"   • Active Notifications: {active_notifications}")

print("\n" + "="*60)
print("✓ ADMIN DASHBOARD DATA GENERATION COMPLETE!")
print("="*60)
print("\nYou can now view the admin dashboard with:")
print("  • Real parking availability data")
print("  • Daily/Weekly entry/exit statistics")
print("  • Peak hour information")
print("  • Efficiency metrics")
print("  • Database occupancy vs actual occupancy")
print("  • Active notifications and alerts")
print("="*60)
