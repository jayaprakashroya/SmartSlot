#!/usr/bin/env python
"""
List all users and delete duplicate user account
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User

print('=' * 70)
print('CHECKING ALL USERS IN DATABASE')
print('=' * 70)

users = User.objects.all()
print(f"\nTotal users: {len(users)}\n")

for user in users:
    status = ""
    if user.is_superuser:
        status = " (ADMIN)"
    elif user.is_staff:
        status = " (STAFF)"
    
    print(f'Username: {user.username}{status}')
    print(f'  Email: {user.email}')
    print(f'  is_active: {user.is_active}')
    print(f'  is_staff: {user.is_staff}')
    print(f'  is_superuser: {user.is_superuser}')
    print()

# Find and delete duplicate user accounts created by other admin logins
print('=' * 70)
print('CLEANING UP DUPLICATE USER ACCOUNTS')
print('=' * 70)

# Look for regular users (non-admin) with admin@smartparking.com email
admin_email_users = User.objects.filter(email='admin@smartparking.com', is_superuser=False)

if admin_email_users.exists():
    print(f"\nFound {admin_email_users.count()} non-admin user(s) with admin@smartparking.com")
    for user in admin_email_users:
        print(f"  Deleting: {user.username} (email: {user.email})")
        user.delete()
        print(f"  ✓ Deleted successfully")
else:
    print("\n✓ No duplicate user accounts found")

# Find and delete other non-admin users if needed
print("\n" + '=' * 70)
print('REMAINING USERS')
print('=' * 70)

remaining_users = User.objects.all()
print(f"\nTotal users after cleanup: {len(remaining_users)}\n")

for user in remaining_users:
    status = ""
    if user.is_superuser:
        status = " [ADMIN]"
    elif user.is_staff:
        status = " [STAFF]"
    else:
        status = " [USER]"
    
    print(f'{user.username}{status}')
    print(f'  Email: {user.email}')
    print(f'  Active: {user.is_active}')
    print()

print('=' * 70)
