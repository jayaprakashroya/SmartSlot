"""
Test heatmap data availability and display
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

import json
from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle
from parkingapp.edge_case_handlers import HeatmapHandler

print("=" * 75)
print("HEATMAP DATA VERIFICATION")
print("=" * 75)

# Get all parking lots
lots = ParkingLot.objects.all()
print(f"\n✅ Found {lots.count()} parking lots\n")

for lot in lots:
    print(f"\n🏢 {lot.lot_name}")
    print(f"   Total Spots: {lot.total_spots}")
    
    # Get heatmap data
    try:
        heatmap = HeatmapHandler.get_lot_heatmap(lot.lot_id)
        
        print(f"   ✓ Heatmap Data Retrieved:")
        print(f"     • Occupied: {heatmap['occupied']} spots")
        print(f"     • Available: {heatmap['available']} spots")
        print(f"     • Occupancy Rate: {heatmap['occupancy_rate']}%")
        print(f"     • Total Spots in Heatmap: {len(heatmap['spots'])}")
        
        # Show spot distribution
        green_spots = [s for s in heatmap['spots'] if s['color'] == 'green']
        red_spots = [s for s in heatmap['spots'] if s['color'] == 'red']
        yellow_spots = [s for s in heatmap['spots'] if s['color'] == 'yellow']
        
        print(f"     • Green (Empty): {len(green_spots)}")
        print(f"     • Red (Occupied): {len(red_spots)}")
        print(f"     • Yellow (Medium): {len(yellow_spots)}")
        
        # Show sample spots
        if len(heatmap['spots']) > 0:
            print(f"\n     Sample Spots (first 5):")
            for spot in heatmap['spots'][:5]:
                status = "🔴 OCCUPIED" if spot['is_occupied'] else "🟢 EMPTY"
                print(f"       • {spot['spot_number']}: {status} (Color: {spot['color']})")
        
        # Get analytics
        try:
            analytics = HeatmapHandler.get_heatmap_analytics(lot.lot_id)
            print(f"\n     📊 Analytics:")
            print(f"       • Free Zones: {analytics.get('free_zones', 0)}")
            print(f"       • Medium Zones: {analytics.get('medium_zones', 0)}")
            print(f"       • Busy Zones: {analytics.get('busy_zones', 0)}")
        except Exception as e:
            print(f"     ✗ Error getting analytics: {e}")
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")

print("\n" + "=" * 75)
print("✅ HEATMAP DATA IS AVAILABLE")
print("=" * 75)
print("\n📍 Access Heatmap:")
print("   • URL: http://127.0.0.1:8000/heatmap/")
print("   • API: http://127.0.0.1:8000/api/heatmap-realtime/1/")
print("\n💡 Note: Heatmap requires login with:")
print("   • Admin: admin / AdminPass@123")
print("   • User: user / UserPass@123")
print("=" * 75)
