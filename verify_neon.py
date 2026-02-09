import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
import django; django.setup()
from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle, Vehicle, User_details
print(f"Lots: {ParkingLot.objects.count()}")
print(f"Spots: {ParkingSpot.objects.count()}")
print(f"Vehicles: {Vehicle.objects.count()}")
print(f"Parked: {ParkedVehicle.objects.filter(checkout_time__isnull=True).count()}")
print(f"Users: {User_details.objects.count()}")
