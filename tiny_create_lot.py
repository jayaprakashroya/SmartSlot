import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot

lot, created = ParkingLot.objects.get_or_create(lot_name='Tiny Demo Lot', defaults={'total_spots':10})
print('lot_created', created, 'lot_id', getattr(lot, 'lot_id', None))
