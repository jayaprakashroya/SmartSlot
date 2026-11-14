#!/usr/bin/env python
"""
Script to create sample admin and user accounts for testing
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from parkingapp.models import User_details

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@smartslot.com'
ADMIN_PASSWORD = 'Admin@12345'

# Regular user credentials
USER_USERNAME = 'user'
USER_EMAIL = 'user@smartslot.com'
USER_PASSWORD = 'User@12345'

def create_sample_users():
    print("=" * 60)
    print("Creating Sample Users for SmartSlot")
    print("=" * 60)
    
    # Create Admin User
    try:
        admin_user = User.objects.get(username=ADMIN_USERNAME)
        print(f"✓ Admin user '{ADMIN_USERNAME}' already exists")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name='Admin',
            last_name='User'
        )
        print(f"✓ Created superuser: {ADMIN_USERNAME}")
    
    # Create Regular User
    try:
        user = User.objects.get(username=USER_USERNAME)
        print(f"✓ Regular user '{USER_USERNAME}' already exists")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=USER_USERNAME,
            email=USER_EMAIL,
            password=USER_PASSWORD,
            first_name='John',
            last_name='Doe'
        )
        print(f"✓ Created regular user: {USER_USERNAME}")
        
        # Create UserDetails for regular user
        try:
            User_details.objects.create(
                user=user,
                phone='+1234567890',
                address='123 Main St, City, State',
                city='New York',
                state='NY',
                country='USA',
                postal_code='10001'
            )
            print(f"✓ Created user profile for {USER_USERNAME}")
        except Exception as e:
            print(f"⚠ Could not create user details: {e}")
    
    print("\n" + "=" * 60)
    print("LOGIN CREDENTIALS")
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
    print("✓ Sample users created successfully!")
    print("=" * 60)

if __name__ == '__main__':
    create_sample_users()
