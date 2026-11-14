#!/usr/bin/env python
"""
Script to set up local developer credentials for SmartSlot
Email-based login for User and Admin accounts
"""
import os
import django
import hashlib
from django.contrib.auth.hashers import make_password

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import User_details

# Define credentials
CREDENTIALS = {
    'user': {
        'email': 'user@smartparking.com',
        'password': 'UserPass@123',
        'is_admin': False
    },
    'admin': {
        'email': 'admin@smartparking.com',
        'password': 'AdminPass@123',
        'is_admin': True
    }
}

def setup_credentials():
    print("=" * 70)
    print("🔐 SmartSlot Local Developer Credentials Setup")
    print("=" * 70)
    
    for account_type, creds in CREDENTIALS.items():
        email = creds['email']
        password = creds['password']
        
        # Delete existing user if exists
        User_details.objects.filter(Email=email).delete()
        print(f"\n⏳ Setting up {account_type.upper()} account...")
        
        # Hash the password using Django's password hasher
        hashed_password = make_password(password)
        
        # Create new user
        user = User_details.objects.create(
            Email=email,
            Password=hashed_password
        )
        
        print(f"✅ Created {account_type.upper()} account")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.User_id}")
        print(f"   Login URL: http://localhost:8000/login/")
    
    print("\n" + "=" * 70)
    print("✅ ALL CREDENTIALS SET UP SUCCESSFULLY!")
    print("=" * 70)
    print("\n📝 LOGIN INFORMATION:")
    print("\n👤 REGULAR USER:")
    print(f"   Email: user@smartparking.com")
    print(f"   Password: UserPass@123")
    print(f"   Access: http://localhost:8000/")
    
    print("\n🔑 ADMIN USER:")
    print(f"   Email: admin@smartparking.com")
    print(f"   Password: AdminPass@123")
    print(f"   Access: http://localhost:8000/admin/ (Django Admin)")
    
    print("\n" + "=" * 70)
    print("💡 TIP: Also create Django superuser for admin panel")
    print("   Command: python manage.py createsuperuser")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    try:
        setup_credentials()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
