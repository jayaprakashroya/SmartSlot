#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import User_details

# Create test user
print("Creating test user...")
try:
    # Check if user already exists
    existing = User_details.objects.filter(Email="admin").first()
    if existing:
        print(f"User 'admin' already exists. Updating password...")
        existing.Password = "4321"
        existing.save()
        print(f"✓ Updated: admin / 4321")
    else:
        new_user = User_details.objects.create(Email="admin", Password="4321")
        print(f"✓ Created: admin / 4321")
    
    # Show all users
    print("\n--- All Users in Database ---")
    users = User_details.objects.all()
    for user in users:
        pwd_mask = '*' * len(user.Password) if user.Password else 'None'
        print(f"  • {user.Email} : {pwd_mask}")
    
except Exception as e:
    print(f"✗ Error: {e}")
