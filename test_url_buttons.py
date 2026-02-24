import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.test import Client
from django.urls import reverse, NoReverseMatch

client = Client()

url_names = [
    'home','about','contact','feedback','login','logout','admin_login','signup',
    'dashboard','detect_numberplate','smart_car_parking','video',
    'find_my_car','parking_lot_status','vehicle_history','api_find_vehicle',
    # not listing all api endpoints
]

print('Checking page availability for core buttons:')
for name in url_names:
    try:
        url = reverse(name)
    except NoReverseMatch:
        print(f"{name} -> REVERSE FAIL")
        continue
    resp = client.get(url)
    print(f"{name} -> {url} -> {resp.status_code}")
