import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
import django; django.setup()
from parkingapp.edge_case_handlers import HeatmapHandler
from parkingapp.models import ParkingLot

if ParkingLot.objects.exists():
    lot = ParkingLot.objects.first()
    heatmap = HeatmapHandler.get_lot_heatmap(lot.lot_id)
    print(f"Lot ID: {heatmap.get('lot_id')}")
    print(f"Lot Name: {heatmap.get('lot_name')}")
    print(f"Total Spots: {heatmap.get('total_spots')}")
    print(f"Occupied: {heatmap.get('occupied')}")
    print(f"Available: {heatmap.get('available')}")
    print(f"Occupancy Rate: {heatmap.get('occupancy_rate')}%")
    print(f"Number of spots in heatmap: {len(heatmap.get('spots', []))}")
    if heatmap.get('spots'):
        print(f"First spot: {heatmap['spots'][0]}")
else:
    print("No parking lots found")
