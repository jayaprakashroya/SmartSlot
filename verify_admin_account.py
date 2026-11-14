#!/usr/bin/env python
"""
Verify admin user exists and recreate if needed
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print('=' * 70)
print('VERIFYING ADMIN ACCOUNT')
print('=' * 70)

ADMIN_EMAIL = 'admin@smartparking.com'
ADMIN_PASSWORD = 'AdminPass@123'

# Check if admin user exists
admin_exists = User.objects.filter(email=ADMIN_EMAIL, is_superuser=True).exists()

if admin_exists:
    print(f"\n✓ Admin user already exists with email: {ADMIN_EMAIL}")
    admin = User.objects.get(email=ADMIN_EMAIL, is_superuser=True)
else:
    print(f"\n✗ Admin user not found - Creating new one...")
    admin = User.objects.create_superuser(
        username=ADMIN_EMAIL,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        first_name='Administrator',
        last_name='User'
    )
    print(f"✓ Admin user created successfully")

# Display admin user details
print(f"\nAdmin User Details:")
print(f"  Username: {admin.username}")
print(f"  Email: {admin.email}")
print(f"  Active: {admin.is_active}")
print(f"  Staff: {admin.is_staff}")
print(f"  Superuser: {admin.is_superuser}")

# Test authentication
print(f"\n" + '=' * 70)
print('TESTING AUTHENTICATION')
print('=' * 70)

auth_result = authenticate(username=ADMIN_EMAIL, password=ADMIN_PASSWORD)
if auth_result:
    print(f"\n✓ Authentication successful!")
    print(f"  Credentials work: {auth_result.username}")
else:
    print(f"\n✗ Authentication FAILED - Resetting password...")
    admin.set_password(ADMIN_PASSWORD)
    admin.save()
    print(f"✓ Password reset")
    
    # Test again
    auth_result = authenticate(username=ADMIN_EMAIL, password=ADMIN_PASSWORD)
    if auth_result:
        print(f"✓ Authentication now works!")
    else:
        print(f"✗ Still failing - check credentials")

print(f"\n" + '=' * 70)
print('ADMIN LOGIN CREDENTIALS')
print('=' * 70)
print(f"\nEmail: {ADMIN_EMAIL}")
print(f"Password: {ADMIN_PASSWORD}")
print(f"\nLogin URL: http://localhost:8000/admin-login/")
print(f"\nOnly ADMIN can login with these credentials.")
print(f"Regular users cannot use this account.")
print(f"\n" + '=' * 70)
