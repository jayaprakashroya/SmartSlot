import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
django.setup()
from django.test import Client

client = Client()
print('offline-status', client.get('/api/offline-status/').status_code)
print('check-double-parking', client.get('/api/check-double-parking/').status_code)
print('sync-pending-records', client.get('/api/sync-pending-records/').status_code)
print('search vehicle', client.post('/api/admin/search-vehicle/', data = {'search':'ABC123','type':'vehicle_number'}, content_type='application/json').status_code)
