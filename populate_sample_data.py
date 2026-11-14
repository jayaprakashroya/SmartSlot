#!/usr/bin/env python
"""
Smart Parking System - Sample Data Population Script
"""

import os
import sys
import django
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import User_details, ParkingLot

def main():
    print("=" * 60)
    print("🅿️  Smart Parking System - Sample Data Population")
    print("=" * 60)
    
    try:
        # Create sample users
        print("\nCreating sample users...")
        users_data = [
            {'email': 'john@example.com', 'password': 'password123'},
            {'email': 'jane@example.com', 'password': 'password123'},
            {'email': 'admin@example.com', 'password': 'admin123'},
            {'email': 'mike@example.com', 'password': 'password123'},
            {'email': 'sarah@example.com', 'password': 'password123'},
        ]
        
        for user_data in users_data:
            user, created = User_details.objects.get_or_create(
                Email=user_data['email'],
                defaults={
                    'Password': hashlib.md5(user_data['password'].encode()).hexdigest()[:15]
                }
            )
            if created:
                print(f"  ✓ Created user: {user_data['email']}")
            else:
                print(f"  ℹ User already exists: {user_data['email']}")
        
        # Create sample parking lots
        print("\nCreating sample parking lots...")
        lots_data = [
            {'lot_name': 'Downtown Parking Garage', 'total_spots': 150},
            {'lot_name': 'Shopping Mall Parking', 'total_spots': 250},
            {'lot_name': 'Airport Terminal 1 Parking', 'total_spots': 500},
            {'lot_name': 'Hospital Medical Center Parking', 'total_spots': 100},
            {'lot_name': 'University Campus Parking', 'total_spots': 300},
        ]
        
        for lot_data in lots_data:
            lot, created = ParkingLot.objects.get_or_create(
                lot_name=lot_data['lot_name'],
                defaults={'total_spots': lot_data['total_spots']}
            )
            if created:
                print(f"  ✓ Created lot: {lot_data['lot_name']} ({lot_data['total_spots']} spots)")
            else:
                print(f"  ℹ Lot already exists: {lot_data['lot_name']}")
        
        print("\n" + "=" * 60)
        print("✅ Sample data population completed successfully!")
        print("=" * 60)
        print("\n📊 Sample Data Summary:")
        print(f"  • Users created: {User_details.objects.count()}")
        print(f"  • Parking lots: {ParkingLot.objects.count()}")
        
        print("\n🔐 Test Login Credentials:")
        print("  Admin User:")
        print("    Email: admin@example.com")
        print("    Password: admin123")
        print("\n  Regular Users:")
        print("    Email: john@example.com | Password: password123")
        print("    Email: jane@example.com | Password: password123")
        print("    Email: mike@example.com | Password: password123")
        print("    Email: sarah@example.com | Password: password123")
        
        print("\n🚀 Next Steps:")
        print("  1. Start Django server: python manage.py runserver")
        print("  2. Open http://localhost:8000")
        print("  3. Log in with credentials above")
        print("  4. Start using the application")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
