#!/usr/bin/env python
"""
Check database tables
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.db import connection
from django.apps import apps
from parkingapp.models import Vehicle, ParkingSpot, ParkingLot, ParkedVehicle

def add_demo_spots_all_lots():
    """Add demo parking spots for all parking lots if none exist"""
    from parkingapp.models import ParkingLot, ParkingSpot
    lots = ParkingLot.objects.all()
    for lot in lots:
        if not ParkingSpot.objects.filter(parking_lot=lot).exists():
            for i in range(1, 11):
                ParkingSpot.objects.create(
                    parking_lot=lot,
                    spot_number=i,
                    spot_type='standard',
                    is_occupied=(i % 3 == 0)
                )
    print("Demo spots added for all lots.")

print("=" * 70)
print("DATABASE TABLES CHECK")
print("=" * 70)

# Get all tables in database
with connection.cursor() as cursor:
    if connection.vendor == 'sqlite':
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    elif connection.vendor == 'postgresql':
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    elif connection.vendor == 'mysql':
        cursor.execute("SHOW TABLES;")
    
    tables = [row[0] for row in cursor.fetchall()]

print(f"\nTotal tables found: {len(tables)}")
print("\nAll tables in database:")
for table in sorted(tables):
    print(f"  - {table}")

# Check for parking app tables
print("\n\nLooking for parking app tables...")
required_tables = [
    'parkingapp_vehicle',
    'parkingapp_parkingspot',
    'parkingapp_parkinglot',
    'parkingapp_parkedvehicle',
]

for table in required_tables:
    if table in tables:
        print(f"  ✓ {table}")
    else:
        print(f"  ✗ {table} - MISSING!")

# List all models in parkingapp
print("\n\nAll models in parkingapp app:")
app_config = apps.get_app_config('parkingapp')
for model in app_config.get_models():
    db_table = model._meta.db_table
    exists = db_table in tables
    status = "✓" if exists else "✗"
    print(f"  {status} {model.__name__} (table: {db_table})")

print("\n" + "=" * 70)

if __name__ == "__main__":
    add_demo_spots_all_lots()
