import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
os.environ.setdefault('RANDOMIZE_OCCUPANCY','True')
import django
django.setup()
from parkingapp.models import ParkingLot
from parkingapp.parking_manager import ParkingManager
lot = ParkingLot.objects.first()
if lot:
    print('lot name', lot.lot_name, 'total spots', lot.total_spots)
    for i in range(5):
        status = ParkingManager.get_parking_lot_status(lot)
        print(status['occupied_spots'], status['available_spots'], status['occupancy_rate'])
else:
    print('no lot found')
