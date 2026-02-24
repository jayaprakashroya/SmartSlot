import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
django.setup()
from django.test import Client

c = Client()
resp = c.get('/heatmap/')
print('status', resp.status_code)
text = resp.content.decode('utf-8')
# show snippet around nav
start = text.find('<nav')
end = text.find('</nav>', start) + len('</nav>')
print(text[start:end])
