import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ParkingProject.settings')
django.setup()
from django.test import Client
c = Client()
# simulate logged-in user so logout link should appear if navbar shows it
sess = c.session
sess['user_email'] = 'tester@example.com'
sess.save()
resp = c.get('/heatmap/')
print('heatmap status', resp.status_code)
# debug: output first 500 characters to see where "Login/Sign Up" might appear
text=resp.content.decode('utf-8')
print('---- snippet ----')
print(text[:800])
print('---- end snippet ----')

# find positions of tokens but ignore ones inside <script> or <style>
def strip_scripts_and_styles(html):
    import re
    # remove <script>...</script> and <style>...</style> sections
    html = re.sub(r'<script[\s\S]*?<\/script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style[\s\S]*?<\/style>', '', html, flags=re.IGNORECASE)
    return html

clean = strip_scripts_and_styles(text)

# find tokens in cleaned text
login_pos = clean.find('Login')
signup_pos = clean.find('Sign Up')
logout_pos = clean.find('Logout')
print(f"Login position: {login_pos}, Sign Up position: {signup_pos}, Logout position: {logout_pos}")
if signup_pos != -1:
    start = max(0, signup_pos-60)
    end = signup_pos + 120
    print('context around Sign Up:', clean[start:end])

if login_pos != -1:
    start = max(0, login_pos-60)
    end = login_pos + 120
    print('context around Login:', clean[start:end])

if 'Login' in clean or 'Sign Up' in clean:
    print('Auth links still present in cleaned HTML')
else:
    print('Auth links removed (cleaned HTML)')
if 'Logout' in clean:
    print('Logout link is present (good if logged-in)')
else:
    print('Logout link missing (may mean user not detected)')
