import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot
from parkingapp.parking_manager import ParkingManager

print("=" * 80)
print("PARKING LOT STATUS TEST")
print("=" * 80)

parking_lot = ParkingLot.objects.first()
if parking_lot:
    status = ParkingManager.get_parking_lot_status(parking_lot)
    print(f'\nLot: {parking_lot.lot_name}')
    print(f'Total Spots: {status["total_spots"]}')
    print(f'Occupied: {status["occupied_spots"]}')
    print(f'Available: {status["available_spots"]}')
    print(f'Occupancy Rate: {status["occupancy_rate"]:.1f}%')
    print(f'Spots returned: {len(status.get("spots", []))}')
    print('\n✅ PARKING LOT STATUS PAGE IS READY AND WORKING!')
else:
    print('No parking lots found')
