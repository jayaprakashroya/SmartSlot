#!/usr/bin/env python
"""
Script to update user passwords to match password manager credentials
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User

# New credentials from password manager
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'AdminPass@123'
ADMIN_EMAIL = 'admin@smartparking.com'

USER_USERNAME = 'user'
USER_PASSWORD = 'UserPass@123'
USER_EMAIL = 'user@smartparking.com'

def update_passwords():
    print("=" * 60)
    print("Updating User Passwords")
    print("=" * 60)
    
    # Update Admin User
    try:
        admin = User.objects.get(username=ADMIN_USERNAME)
        admin.set_password(ADMIN_PASSWORD)
        admin.email = ADMIN_EMAIL
        admin.save()
        print(f"✓ Updated admin password")
    except User.DoesNotExist:
        print(f"✗ Admin user not found")
    
    # Update Regular User
    try:
        user = User.objects.get(username=USER_USERNAME)
        user.set_password(USER_PASSWORD)
        user.email = USER_EMAIL
        user.save()
        print(f"✓ Updated user password")
    except User.DoesNotExist:
        print(f"✗ User not found")
    
    print("\n" + "=" * 60)
    print("UPDATED LOGIN CREDENTIALS")
    print("=" * 60)
    print("\n🔐 ADMIN ACCOUNT:")
    print(f"   Username: {ADMIN_USERNAME}")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print(f"   Access: http://localhost:8000/admin/")
    
    print("\n👤 REGULAR USER ACCOUNT:")
    print(f"   Username: {USER_USERNAME}")
    print(f"   Email: {USER_EMAIL}")
    print(f"   Password: {USER_PASSWORD}")
    print(f"   Access: http://localhost:8000/")
    
    print("\n" + "=" * 60)
    print("✓ Passwords updated successfully!")
    print("=" * 60)

if __name__ == '__main__':
    update_passwords()
