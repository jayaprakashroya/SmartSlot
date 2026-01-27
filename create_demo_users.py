#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from parkingapp.models import User_details

print("\n" + "="*60)
print("CREATING DEMO USER ACCOUNTS")
print("="*60)

# Create Django superuser for admin
try:
    admin_user, created = User.objects.get_or_create(
        username='admin@smartparking.com',
        defaults={
            'email': 'admin@smartparking.com',
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Admin',
            'last_name': 'User'
        }
    )
    if created:
        admin_user.set_password('AdminPass@123')
        admin_user.save()
        print("\n✓ Django Admin account created successfully!")
        print(f"  Email: admin@smartparking.com")
        print(f"  Password: AdminPass@123")
    else:
        print("\n⚠ Django Admin account already exists")
except Exception as e:
    print(f"\n✗ Error creating Django admin: {e}")

# Create regular user in custom User_details table
try:
    import hashlib
    
    # Use very short hash - MD5 (32 chars) which should fit
    password_plain = 'UserPass@123'
    # Create a short hashed version using just first 15 chars of hash
    short_hash = hashlib.md5(password_plain.encode()).hexdigest()[:15]
    
    regular_user, created = User_details.objects.get_or_create(
        Email='user@smartparking.com',
        defaults={
            'Password': short_hash,
        }
    )
    if created:
        print("\n✓ Regular user account created successfully!")
        print(f"  Email: user@smartparking.com")
        print(f"  Password: UserPass@123")
    else:
        print("\n⚠ Regular user account already exists")
except Exception as e:
    print(f"\n✗ Error creating regular user: {e}")

print("\n" + "="*60)
print("LOGIN CREDENTIALS FOR DEMONSTRATION")
print("="*60)
print("\n📌 ADMIN LOGIN (SmartSlot Admin Panel):")
print("   URL: http://127.0.0.1:8000/admin-login")
print("   Email: admin@smartparking.com")
print("   Password: AdminPass@123")
print("\n📌 REGULAR USER LOGIN (Main Application):")
print("   URL: http://127.0.0.1:8000/login")
print("   Email: user@smartparking.com")
print("   Password: UserPass@123")
print("\n📌 DJANGO ADMIN PANEL:")
print("   URL: http://127.0.0.1:8000/admin")
print("   Username: admin@smartparking.com")
print("   Password: AdminPass@123")
print("\n" + "="*60)
print("✓ Ready for testing and presentation!")
print("="*60 + "\n")
