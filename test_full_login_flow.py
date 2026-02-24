#!/usr/bin/env python
"""
Full admin login simulation with Django test client
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("=" * 70)
print("FULL ADMIN LOGIN SIMULATION")
print("=" * 70)

# Verify admin user exists
print("\n1. CHECKING ADMIN USER...")
try:
    admin = User.objects.get(username='admin')
    print(f"   ✓ Admin user found: {admin.username}")
    print(f"     Email: {admin.email}")
    print(f"     is_active: {admin.is_active}")
    print(f"     is_staff: {admin.is_staff}")
    print(f"     is_superuser: {admin.is_superuser}")
except User.DoesNotExist:
    print("   ✗ Admin user not found!")
    exit(1)

# Test direct authentication
print("\n2. TESTING DIRECT AUTHENTICATION...")
authenticated_user = authenticate(username='admin', password='Admin@12345')
if authenticated_user:
    print(f"   ✓ Direct authentication successful")
    print(f"     User: {authenticated_user.username}")
else:
    print(f"   ✗ Direct authentication FAILED")

# Test with Django test client
print("\n3. TESTING WITH DJANGO TEST CLIENT...")
client = Client()

# First, just GET the login page
print("\n   a) GET /admin-login/")
response = client.get('/admin-login/')
if response.status_code == 200:
    print(f"      ✓ Page found (status: {response.status_code})")
else:
    print(f"      ✗ Page not found (status: {response.status_code})")

# Now POST the login form
print("\n   b) POST login form")
login_data = {
    'email': 'admin',
    'password': 'Admin@12345',
}
response = client.post('/admin-login/', login_data)
print(f"      Status: {response.status_code}")
print(f"      URL after POST: {response.wsgi_request.path if hasattr(response, 'wsgi_request') else 'N/A'}")

# Check if we got redirected
if response.status_code in [301, 302, 303, 307, 308]:
    print(f"      ✓ Got redirect (status: {response.status_code})")
    if hasattr(response, 'url'):
        print(f"        Redirect to: {response.url}")
elif response.status_code == 200:
    print(f"      Status: 200 OK (may be re-rendering login form with errors)")
    # Check for messages in response
    if 'messages' in response.context:
        for message in response.context['messages']:
            print(f"        Message: {message}")

# Check if user is authenticated in client session
print("\n   c) Checking client session...")
if response.wsgi_request.user.is_authenticated:
    print(f"      ✓ User is authenticated in session")
    print(f"        Username: {response.wsgi_request.user.username}")
    print(f"        is_staff: {response.wsgi_request.user.is_staff}")
    print(f"        is_superuser: {response.wsgi_request.user.is_superuser}")
else:
    print(f"      ✗ User is NOT authenticated in session")
    print(f"      Current user: Anonymous")

# Try accessing admin dashboard
print("\n   d) Testing admin dashboard access...")
response2 = client.get('/admin-dashboard/')
print(f"      Status: {response2.status_code}")
if response2.status_code == 200:
    print(f"      ✓ Admin dashboard accessible")
elif response2.status_code in [301, 302, 303, 307, 308]:
    print(f"      Redirect status: {response2.status_code}")
    if hasattr(response2, 'url'):
        print(f"      Redirected to: {response2.url}")
else:
    print(f"      Error status: {response2.status_code}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nIf admin login is working:")
print("  - Status code should be 302 (redirect)")
print("  - User should be authenticated in session")
print("  - Dashboard should be accessible (status 200)")
print("\n" + "=" * 70)
