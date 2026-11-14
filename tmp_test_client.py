import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.test import Client

client = Client()
print('GET /admin-login/')
resp = client.get('/admin-login/')
print(resp.status_code, 'len', len(resp.content))

print('\nPOST empty form')
resp2 = client.post('/admin-login/', {'email':'','password':''})
print(resp2.status_code)
print(resp2.content.decode('utf-8')[:500])
