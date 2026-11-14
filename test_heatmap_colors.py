#!/usr/bin/env python
"""Test and debug heatmap colors and occupancy calculation"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle
from parkingapp.edge_case_handlers import HeatmapHandler
from django.utils import timezone

def test_heatmap():
    """Test heatmap generation and color assignment"""
    
    print("=" * 70)
    print("HEATMAP COLOR & OCCUPANCY TEST")
    print("=" * 70)
    
    # Get first parking lot
    lot = ParkingLot.objects.first()
    
    if not lot:
        print("❌ No parking lots found in database")
        return
    
    print(f"\n📍 Testing Lot: {lot.lot_name}")
    print(f"📊 Total Spots: {lot.total_spots}")
    
    # Get heatmap data
    heatmap = HeatmapHandler.get_lot_heatmap(lot.lot_id)
    
    print(f"\n✅ HEATMAP RESULTS:")
    print(f"  Occupied: {heatmap['occupied']} spots (RED)")
    print(f"  Available: {heatmap['available']} spots (GREEN)")
    print(f"  Occupancy Rate: {heatmap['occupancy_rate']}%")
    
    # Show spot details
    print(f"\n📋 SPOT DETAILS (First 10):")
    print("-" * 70)
    print(f"{'Spot':<8} {'Status':<12} {'Color':<10} {'Occupancy':<12} {'Plate':<15}")
    print("-" * 70)
    
    for spot in heatmap['spots'][:10]:
        status = "OCCUPIED" if spot['is_occupied'] else "EMPTY"
        plate = spot['vehicle_plate'] if spot['vehicle_plate'] else "N/A"
        print(f"{spot['spot_number']:<8} {status:<12} {spot['color']:<10} {spot['occupancy']}%{'':<9} {plate:<15}")
    
    print("-" * 70)
    
    # Test database queries
    print(f"\n🔍 DATABASE VALIDATION:")
    
    # Count occupied spots
    occupied_count = ParkedVehicle.objects.filter(
        checkout_time__isnull=True
    ).count()
    print(f"  ParkedVehicle records (active): {occupied_count}")
    
    # Count spots with active vehicles
    spots_with_vehicles = ParkingSpot.objects.filter(
        parkedvehicle__checkout_time__isnull=True
    ).distinct().count()
    print(f"  Spots with active vehicles: {spots_with_vehicles}")
    
    # Show status of each spot
    print(f"\n🟢 GREEN (EMPTY) SPOTS:")
    green_spots = [s for s in heatmap['spots'] if s['color'] == 'green']
    if green_spots:
        for spot in green_spots[:5]:
            print(f"  ✓ {spot['spot_number']} - {spot['occupancy']}% occupied")
        if len(green_spots) > 5:
            print(f"  ... and {len(green_spots) - 5} more empty spots")
    else:
        print("  ❌ NO EMPTY SPOTS FOUND!")
    
    print(f"\n🔴 RED (OCCUPIED) SPOTS:")
    red_spots = [s for s in heatmap['spots'] if s['color'] == 'red']
    if red_spots:
        for spot in red_spots[:5]:
            print(f"  ✓ {spot['spot_number']} - {spot['occupancy']}% occupied - {spot['vehicle_plate']}")
        if len(red_spots) > 5:
            print(f"  ... and {len(red_spots) - 5} more occupied spots")
    else:
        print("  ✓ NO OCCUPIED SPOTS")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_heatmap()
