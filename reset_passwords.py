#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User

print("="*60)
print("RESETTING USER PASSWORDS")
print("="*60)

# Reset admin password
admin = User.objects.get(username='admin')
admin.set_password('Admin@12345')
admin.save()
print(f"✓ Reset admin password to: Admin@12345")

# Reset user password
user = User.objects.get(username='user')
user.set_password('User@12345')
user.save()
print(f"✓ Reset user password to: User@12345")

# Test authentication
from django.contrib.auth import authenticate

print("\n" + "="*60)
print("TESTING AUTHENTICATION")
print("="*60)

test_admin = authenticate(username='admin', password='Admin@12345')
if test_admin:
    print(f"✓ Admin login works: {test_admin.username}")
else:
    print("✗ Admin login still fails")

test_user = authenticate(username='user', password='User@12345')
if test_user:
    print(f"✓ User login works: {test_user.username}")
else:
    print("✗ User login still fails")

print("\n" + "="*60)
print("CREDENTIALS READY")
print("="*60)
print("\nAdmin:")
print("  Username: admin")
print("  Password: Admin@12345")
print("  URL: http://localhost:8000/admin/\n")
print("User:")
print("  Username: user")
print("  Password: User@12345")
print("  URL: http://localhost:8000/\n")
