#!/usr/bin/env python
"""
Comprehensive Sample Data Population Script
Populates parking lots, spots, vehicles, and occupancy data for testing
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from parkingapp.models import (
    ParkingLot, ParkingSpot, Vehicle, ParkedVehicle, 
    ParkingAnalytics
)

def create_parking_lots():
    """Create multiple parking lots with different names and capacities"""
    lot_configs = [
        {'lot_name': 'Downtown Plaza', 'total_spots': 120},
        {'lot_name': 'Airport Terminal A', 'total_spots': 200},
        {'lot_name': 'Shopping Mall West', 'total_spots': 150},
        {'lot_name': 'Office Building Central', 'total_spots': 100},
        {'lot_name': 'Hospital Emergency', 'total_spots': 80},
        {'lot_name': 'Stadium North Gate', 'total_spots': 250},
    ]
    
    lots = []
    for config in lot_configs:
        lot, created = ParkingLot.objects.get_or_create(
            lot_name=config['lot_name'],
            defaults={'total_spots': config['total_spots']}
        )
        lots.append(lot)
        status = "Created" if created else "Already exists"
        print(f"✓ {config['lot_name']}: {config['total_spots']} spots - {status}")
    
    return lots


def create_parking_spots(lots):
    """Create parking spots for each lot with mixed types"""
    spot_types = ['regular', 'reserved', 'handicap', 'vip']
    total_created = 0
    
    for lot in lots:
        # Create spots for this lot
        for spot_num in range(1, lot.total_spots + 1):
            # Alternate between spot types
            spot_type = spot_types[spot_num % len(spot_types)]
            
            # Create grid-based positions (simulating parking lot layout)
            row = (spot_num - 1) // 10
            col = (spot_num - 1) % 10
            x_pos = 100 + (col * 120)
            y_pos = 100 + (row * 60)
            
            spot_number = f"{chr(65 + row)}{col + 1}"  # A1, A2, B1, etc.
            
            spot, created = ParkingSpot.objects.get_or_create(
                parking_lot=lot,
                spot_number=spot_number,
                defaults={
                    'spot_type': spot_type,
                    'x_position': x_pos,
                    'y_position': y_pos,
                    'spot_width': 107,
                    'spot_height': 48
                }
            )
            if created:
                total_created += 1
        
        print(f"✓ {lot.lot_name}: {lot.total_spots} spots created/verified")
    
    return total_created


def create_sample_vehicles(count=50):
    """Create sample vehicles"""
    license_plates = [
        'ABC123', 'XYZ789', 'DEF456', 'GHI789', 'JKL012',
        'MNO345', 'PQR678', 'STU901', 'VWX234', 'YZA567',
        'BCD890', 'EFG123', 'HIJ456', 'KLM789', 'NOP012',
        'QRS345', 'TUV678', 'WXY901', 'ZAB234', 'CDE567',
        'FGH890', 'IJK123', 'LMN456', 'OPQ789', 'RST012',
        'UVW345', 'XYZ678', 'ABC901', 'DEF234', 'GHI567',
        'JKL890', 'MNO123', 'PQR456', 'STU789', 'VWX012',
        'YZA345', 'BCD678', 'EFG901', 'HIJ234', 'KLM567',
        'NOP890', 'QRS123', 'TUV456', 'WXY789', 'ZAB012',
        'CDE345', 'FGH678', 'IJK901', 'LMN234', 'OPQ567',
    ]
    
    vehicles = []
    for plate in license_plates[:count]:
        vehicle, created = Vehicle.objects.get_or_create(
            license_plate=plate,
            defaults={
                'vehicle_type': random.choice(['car', 'truck', 'motorcycle', 'bus']),
                'owner_name': f"Owner{plate}",
                'owner_phone': f"555-{random.randint(1000, 9999)}",
                'color': random.choice(['Red', 'Blue', 'White', 'Black', 'Silver', 'Gray'])
            }
        )
        vehicles.append(vehicle)
    
    print(f"✓ Created {len(vehicles)} sample vehicles")
    return vehicles


def create_occupancy_data(lots, vehicles):
    """Create ParkedVehicle entries to simulate occupancy"""
    vehicle_idx = 0
    total_occupied = 0
    assigned_vehicles = set()  # Track which vehicles already have active parking
    
    for lot in lots:
        # Calculate how many spots to fill (varies per lot)
        occupancy_percent = random.choice([30, 50, 75, 90])  # Different occupancy rates
        spots_to_fill = int(lot.total_spots * occupancy_percent / 100)
        
        # Get all spots for this lot
        spots = list(lot.spots.all())
        random.shuffle(spots)
        
        # Create occupancy data - IMPORTANT: Each vehicle can only be parked once
        for i, spot in enumerate(spots[:spots_to_fill]):
            # Find a vehicle that isn't already actively parked
            attempts = 0
            vehicle = None
            while attempts < len(vehicles):
                candidate = vehicles[vehicle_idx % len(vehicles)]
                vehicle_idx += 1
                attempts += 1
                
                # Only assign if this vehicle doesn't have an active parking session
                if candidate.license_plate not in assigned_vehicles:
                    vehicle = candidate
                    assigned_vehicles.add(vehicle.license_plate)
                    break
            
            if not vehicle:
                # If all vehicles are assigned, skip this spot
                continue
            
            # Create active parking session (no checkout_time)
            checkin_time = datetime.now() - timedelta(minutes=random.randint(5, 180))
            
            # Ensure this vehicle doesn't already have an active parking session elsewhere
            existing = ParkedVehicle.objects.filter(
                vehicle=vehicle,
                checkout_time__isnull=True
            ).first()
            
            if existing:
                # This shouldn't happen now, but just in case
                assigned_vehicles.discard(vehicle.license_plate)
                continue
            
            parked = ParkedVehicle.objects.create(
                vehicle=vehicle,
                parking_spot=spot,
                parking_lot=lot,
                checkin_time=checkin_time,
                checkout_time=None,
                parking_fee=Decimal(random.uniform(2.50, 15.00)),
                payment_status='pending'
            )
            total_occupied += 1
        
        occupied_count = ParkedVehicle.objects.filter(
            parking_lot=lot,
            checkout_time__isnull=True
        ).count()
        available = lot.total_spots - occupied_count
        occupancy = (occupied_count / lot.total_spots) * 100
        
        print(f"✓ {lot.lot_name}: {occupied_count}/{lot.total_spots} occupied ({occupancy:.1f}%) - {available} available")
    
    return total_occupied


def create_analytics_data(lots):
    """Create ParkingAnalytics for heatmap visualization"""
    today = datetime.now().date()
    total_created = 0
    
    for lot in lots:
        # Create analytics for today and past days
        for days_back in range(0, 7):
            analytics_date = today - timedelta(days=days_back)
            
            # Get actual occupancy count
            occupied_count = ParkedVehicle.objects.filter(
                parking_lot=lot,
                checkout_time__isnull=True
            ).count()
            
            occupancy_percent = int((occupied_count / lot.total_spots) * 100) if lot.total_spots > 0 else 0
            
            analytics, created = ParkingAnalytics.objects.get_or_create(
                parking_lot=lot,
                date=analytics_date,
                defaults={
                    'total_sessions': random.randint(15, 60),
                    'peak_occupancy_percent': min(100, occupancy_percent + random.randint(-10, 20)),
                    'average_duration_minutes': random.randint(45, 240),
                    'total_revenue': Decimal(random.uniform(100, 500)),
                    'peak_hour': random.randint(9, 17)
                }
            )
            if created:
                total_created += 1
        
        print(f"✓ {lot.lot_name}: Analytics data created for {lot.lot_name}")
    
    return total_created


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("PARKING SYSTEM - SAMPLE DATA POPULATION")
    print("="*70 + "\n")
    
    try:
        # Step 1: Create parking lots
        print("📍 Creating parking lots...")
        lots = create_parking_lots()
        print()
        
        # Step 2: Create parking spots
        print("🅿️  Creating parking spots...")
        spots_created = create_parking_spots(lots)
        print()
        
        # Step 3: Create sample vehicles
        print("🚗 Creating sample vehicles...")
        vehicles = create_sample_vehicles()
        print()
        
        # Step 4: Create occupancy data
        print("📊 Populating occupancy data...")
        occupied = create_occupancy_data(lots, vehicles)
        print()
        
        # Step 5: Create analytics
        print("📈 Creating analytics data...")
        analytics = create_analytics_data(lots)
        print()
        
        # Summary
        print("="*70)
        print("✅ SAMPLE DATA POPULATION COMPLETE")
        print("="*70)
        print(f"✓ Parking Lots Created: {len(lots)}")
        print(f"✓ Parking Spots Created: {spots_created}")
        print(f"✓ Sample Vehicles Created: {len(vehicles)}")
        print(f"✓ Occupancy Records Created: {occupied}")
        print(f"✓ Analytics Records Created: {analytics}")
        print("="*70)
        print("\n✨ Sample data is ready! Navigate to:")
        print("   • Parking Status: View all lots with occupancy")
        print("   • Heatmap: See occupancy visualization")
        print("   • Dashboard: Check analytics metrics")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during population: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
