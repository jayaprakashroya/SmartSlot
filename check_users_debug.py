#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User

# List all users
users = User.objects.all()
print(f"Total users in database: {users.count()}\n")

for user in users:
    print(f"Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Is Active: {user.is_active}")
    print(f"  Is Staff: {user.is_staff}")
    print(f"  Is Superuser: {user.is_superuser}")
    print()

# Try to authenticate
from django.contrib.auth import authenticate

print("\n" + "="*50)
print("Testing Authentication")
print("="*50)

test_user = authenticate(username='admin', password='Admin@12345')
if test_user:
    print(f"✓ Admin auth successful: {test_user.username}")
else:
    print("✗ Admin auth failed")

test_user2 = authenticate(username='user', password='User@12345')
if test_user2:
    print(f"✓ User auth successful: {test_user2.username}")
else:
    print("✗ User auth failed")
