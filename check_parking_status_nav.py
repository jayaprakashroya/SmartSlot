import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
django.setup()
from django.test import Client
c = Client()
# pretend we're authenticated so logout should appear
sess = c.session
sess['user_email'] = 'tester@example.com'
sess.save()
for path in ['/parking-lot-status/', '/parking-lot-status/1/']:
    resp = c.get(path)
    print(f'{path} status', resp.status_code)
    text = resp.content.decode('utf-8')
    # strip scripts and styles
    import re
    clean = re.sub(r'<script[\s\S]*?<\/script>', '', text, flags=re.IGNORECASE)
    clean = re.sub(r'<style[\s\S]*?<\/style>', '', clean, flags=re.IGNORECASE)
    for token in ['Login','Sign Up','Logout']:
        pos = clean.find(token)
        print(f'  {token} position', pos)
        if pos != -1:
            start = max(0,pos-40)
            end = pos+80
            print('    context:', clean[start:end].replace('\n',' '))
    if 'Sign Up' in clean or 'Login' in clean:
        print('  Auth tokens still present (clean)')
    else:
        print('  Clean page clear')
    if 'Logout' in clean:
        print('  Logout link visible (expected)')
    else:
        print('  Logout missing (unexpected)')
