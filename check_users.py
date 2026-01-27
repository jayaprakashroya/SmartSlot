#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import User_details

# Show all users
users = User_details.objects.all()
print("="*60)
print("Total users in database:", users.count())
print("="*60)

if users.count() > 0:
    print("\n--- All Users ---")
    for user in users:
        pwd_mask = '*' * len(user.Password) if user.Password else 'None'
        print(f"ID: {user.User_id}, Email: {user.Email}, Password: {pwd_mask}")
else:
    print("\nNo users found. Creating test users...")
    test_user1 = User_details.objects.create(Email="test@example.com", Password="test123")
    test_user2 = User_details.objects.create(Email="user@smartslot.com", Password="password123")
    print(f"✓ Created: {test_user1.Email}")
    print(f"✓ Created: {test_user2.Email}")

print("\n" + "="*60)
print("User_details table location: 'user_details' in MySQL database")
print("="*60)
