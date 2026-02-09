#!/usr/bin/env python
"""
Populate all sample data into Neon database
- User accounts (admin, user)
- Parking lots (3)
- Parking spots (90 total across all lots)
- Vehicles (10)
- Parked vehicles (8 active)
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from parkingapp.models import User_details, ParkingLot, ParkingSpot, Vehicle, ParkedVehicle

def populate_users():
    """Create Django users and User_details"""
    print("\n📝 Creating users...")
    
    # Admin user
    admin_user, admin_created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@smartslot.com', 'is_staff': True, 'is_superuser': True}
    )
    if admin_created:
        admin_user.set_password('Admin@12345')
        admin_user.save()
        print("  ✓ Created Django admin user")
    else:
        print("  ℹ Admin user already exists")
    
    # Regular user
    user, user_created = User.objects.get_or_create(
        username='user',
        defaults={'email': 'user@smartslot.com'}
    )
    if user_created:
        user.set_password('User@12345')
        user.save()
        print("  ✓ Created Django regular user")
    else:
        print("  ℹ Regular user already exists")
    
    # User_details for custom auth
    admin_details, created = User_details.objects.get_or_create(
        Email='admin@smartslot.com',
        defaults={'Password': 'Admin@12345'}
    )
    if created:
        print("  ✓ Created User_details for admin")
    
    user_details, created = User_details.objects.get_or_create(
        Email='user@smartslot.com',
        defaults={'Password': 'User@12345'}
    )
    if created:
        print("  ✓ Created User_details for user")
    
    print(f"  📊 Total User_details: {User_details.objects.count()}")

def populate_parking_lots():
    """Create parking lots"""
    print("\n🅿️  Creating parking lots...")
    
    lots_data = [
        {'lot_name': 'Downtown Garage', 'total_spots': 30},
        {'lot_name': 'Mall Parking', 'total_spots': 40},
        {'lot_name': 'Airport Terminal', 'total_spots': 50},
    ]
    
    for data in lots_data:
        lot, created = ParkingLot.objects.get_or_create(
            lot_name=data['lot_name'],
            defaults={'total_spots': data['total_spots']}
        )
        if created:
            print(f"  ✓ Created: {data['lot_name']} ({data['total_spots']} spots)")
        else:
            print(f"  ℹ Exists: {data['lot_name']}")
    
    print(f"  📊 Total parking lots: {ParkingLot.objects.count()}")

def populate_parking_spots():
    """Create parking spots for each lot"""
    print("\n📍 Creating parking spots...")
    
    lots = ParkingLot.objects.all()
    total_spots = 0
    
    for lot in lots:
        # Skip if already has spots
        if lot.spots.count() > 0:
            print(f"  ℹ {lot.lot_name} already has {lot.spots.count()} spots")
            continue
        
        for i in range(1, lot.total_spots + 1):
            spot_number = f"{lot.lot_name[0:2].upper()}{i:03d}"  # DG001, DG002, etc.
            try:
                spot, created = ParkingSpot.objects.get_or_create(
                    parking_lot=lot,
                    spot_number=spot_number,
                    defaults={
                        'spot_type': random.choice(['regular', 'reserved', 'handicap']),
                        'x_position': (i % 5) * 100,
                        'y_position': (i // 5) * 100,
                        'spot_width': 107,
                        'spot_height': 48
                    }
                )
                if created:
                    total_spots += 1
            except Exception as e:
                print(f"  ❌ Error creating spot {spot_number}: {e}")
        
        print(f"  ✓ Created {lot.total_spots} spots for {lot.lot_name}")
    
    print(f"  📊 Total parking spots: {ParkingSpot.objects.count()}")

def populate_vehicles():
    """Create sample vehicles"""
    print("\n🚗 Creating vehicles...")
    
    plates = ['ABC123', 'DEF456', 'GHI789', 'JKL012', 'MNO345', 
              'PQR678', 'STU901', 'VWX234', 'YZA567', 'BCD890']
    
    created_count = 0
    for plate in plates:
        vehicle, created = Vehicle.objects.get_or_create(
            license_plate=plate,
            defaults={
                'vehicle_type': random.choice(['car', 'truck', 'motorcycle']),
                'owner_name': f'Owner {plate}',
                'color': random.choice(['black', 'white', 'gray', 'red', 'blue', 'silver'])
            }
        )
        if created:
            created_count += 1
    
    if created_count > 0:
        print(f"  ✓ Created {created_count} new vehicles")
    else:
        print(f"  ℹ All vehicles already exist")
    
    print(f"  📊 Total vehicles: {Vehicle.objects.count()}")

def populate_parked_vehicles():
    """Create sample parked vehicles"""
    print("\n🅿️  Creating parked vehicles (occupancy)...")
    
    lots = ParkingLot.objects.all()
    parked_count = 0
    
    for lot in lots:
        # Get available spots (those without active parking)
        available_spots = []
        for spot in lot.spots.all()[:8]:  # Use first 8 spots
            active_parked = spot.parkedvehicle_set.filter(checkout_time__isnull=True).exists()
            if not active_parked:
                available_spots.append(spot)
        
        # Get available vehicles
        vehicles = list(Vehicle.objects.all()[:8])
        
        # Park vehicles
        for idx, spot in enumerate(available_spots[:len(vehicles)]):
            if idx >= len(vehicles):
                break
            
            vehicle = vehicles[idx]
            
            # Check if vehicle already parked elsewhere
            already_parked = ParkedVehicle.objects.filter(
                vehicle=vehicle,
                checkout_time__isnull=True
            ).exists()
            
            if not already_parked:
                try:
                    parked, created = ParkedVehicle.objects.get_or_create(
                        vehicle=vehicle,
                        parking_spot=spot,
                        defaults={
                            'parking_lot': lot,
                            'checkin_time': datetime.now() - timedelta(hours=random.randint(1, 6)),
                            'checkout_time': None,
                            'parking_fee': random.uniform(2.0, 15.0)
                        }
                    )
                    if created:
                        parked_count += 1
                except Exception as e:
                    print(f"  ⚠ Error parking {vehicle.license_plate}: {e}")
        
        if parked_count > 0:
            print(f"  ✓ Parked {parked_count} vehicles in {lot.lot_name}")
    
    print(f"  📊 Total active parked vehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")

def main():
    print("\n" + "="*60)
    print("🚀 Populating Neon Database with Sample Data")
    print("="*60)
    
    try:
        populate_users()
        populate_parking_lots()
        populate_parking_spots()
        populate_vehicles()
        populate_parked_vehicles()
        
        print("\n" + "="*60)
        print("✅ Data population COMPLETE!")
        print("="*60)
        
        print("\n📊 SUMMARY:")
        print(f"  • User accounts: {User_details.objects.count()}")
        print(f"  • Parking lots: {ParkingLot.objects.count()}")
        print(f"  • Parking spots: {ParkingSpot.objects.count()}")
        print(f"  • Vehicles: {Vehicle.objects.count()}")
        print(f"  • Active parked vehicles: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
        
        print("\n🔐 Test Credentials:")
        print("  Admin: admin / Admin@12345")
        print("  User: user / User@12345")
        
        print("\n🌐 Live URL: https://smartslot-r2kq.onrender.com")
        print("  • Heatmap should now show occupancy")
        print("  • Find parking should work")
        print("  • Payments should be accessible")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
