#!/usr/bin/env python
"""
Script to create/update user accounts with password manager credentials
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

def setup_credentials():
    print("=" * 60)
    print("Setting Up User Accounts")
    print("=" * 60)
    
    # Delete existing users if they exist (clean slate)
    User.objects.filter(username=ADMIN_USERNAME).delete()
    User.objects.filter(username=USER_USERNAME).delete()
    
    # Create Admin User
    admin = User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        first_name='Admin',
        last_name='User'
    )
    print(f"✓ Created admin account: {ADMIN_USERNAME}")
    
    # Create Regular User
    user = User.objects.create_user(
        username=USER_USERNAME,
        email=USER_EMAIL,
        password=USER_PASSWORD,
        first_name='John',
        last_name='Doe'
    )
    print(f"✓ Created user account: {USER_USERNAME}")
    
    print("\n" + "=" * 60)
    print("✅ LOGIN CREDENTIALS (Password Manager Credentials)")
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
    print("✓ All accounts ready!")
    print("=" * 60)

if __name__ == '__main__':
    setup_credentials()
