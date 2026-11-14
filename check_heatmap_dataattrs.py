import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
django.setup()
from django.test import Client
c=Client()
sess=c.session; sess['user_email']='x'; sess.save()
text=c.get('/heatmap/').content.decode('utf-8')
# look for the first few spot divs
import re
matches=re.findall(r'<div class="spot[\s\S]*?">', text)
print('first spot divs:')
for m in matches[:3]:
    print(m)
print('--- raw snippet around spot list ---')
idx=text.find('class="spot"')
print(text[idx:idx+300])
