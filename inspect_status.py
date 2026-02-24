import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
django.setup()
from parkingapp.parking_manager import ParkingManager
from parkingapp.models import ParkingLot
lot=ParkingLot.objects.first()
print('lot', lot)
print(ParkingManager.get_parking_lot_status(lot))
