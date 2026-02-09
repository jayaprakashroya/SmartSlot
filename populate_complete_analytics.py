"""
Complete Analytics and Notifications Data Population
Populates: Notifications, Payments, Reservations, Analytics, and Settings
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import random
from decimal import Decimal

from parkingapp.models import (
    User_details, ParkingLot, Vehicle, ParkingSpot, ParkedVehicle,
    UserNotification, Payment, ParkingReservation, ParkingAnalytics,
    ParkingSession, ParkingLotSettings, PricingRule, CameraStatus
)

def create_sample_notifications():
    """Create sample notifications for users"""
    print("\n🔔 Creating User Notifications...")
    
    try:
        users = User_details.objects.all()[:5]  # Get first 5 users
        
        notification_types = [
            ('spot_available', 'Spot Available', 'A parking spot is now available in Lot A'),
            ('parking_expiring', 'Parking Expiring Soon', 'Your parking session expires in 30 minutes'),
            ('payment_due', 'Payment Due', 'Please complete your parking fee payment'),
            ('reservation_reminder', 'Reservation Reminder', 'Your reservation is confirmed for tomorrow'),
            ('parking_complete', 'Parking Complete', 'Thank you for using SmartSlot'),
            ('promotion', 'Promotion', 'Get 20% off on your next parking session'),
        ]
        
        notification_count = 0
        for user in users:
            for notif_type, title, message in notification_types:
                notification, created = UserNotification.objects.get_or_create(
                    user=user,
                    notification_type=notif_type,
                    title=title,
                    defaults={
                        'message': message,
                        'is_read': random.choice([True, False]),
                        'email_sent': random.choice([True, False]),
                        'sms_sent': random.choice([True, False]),
                        'in_app': True,
                        'sent_at': timezone.now() - timedelta(hours=random.randint(1, 48))
                    }
                )
                if created:
                    notification_count += 1
        
        print(f"✓ Created {notification_count} notifications")
        return notification_count
    
    except Exception as e:
        print(f"✗ Error creating notifications: {str(e)}")
        return 0


def create_sample_payments():
    """Create sample payment records"""
    print("\n💳 Creating Payment Records...")
    
    try:
        sessions = ParkingSession.objects.all()[:10]
        
        payment_count = 0
        for session in sessions:
            # Calculate fee based on duration
            if session.duration_minutes:
                hours = session.duration_minutes / 60
                amount = Decimal(str(round(hours * 212.5, 2)))  # ₹212.50/hour
            else:
                amount = Decimal('425.00')
            
            payment, created = Payment.objects.get_or_create(
                parking_session=session,
                defaults={
                    'user': session.user,
                    'amount': amount,
                    'payment_method': random.choice([
                        'credit_card', 'debit_card', 'digital_wallet', 'cash'
                    ]),
                    'payment_status': random.choice(['success', 'pending', 'paid']),
                    'transaction_id': f"TXN{random.randint(100000, 999999)}",
                    'paid_at': timezone.now() if random.choice([True, False]) else None
                }
            )
            if created:
                payment_count += 1
        
        print(f"✓ Created {payment_count} payment records")
        return payment_count
    
    except Exception as e:
        print(f"✗ Error creating payments: {str(e)}")
        return 0


def create_sample_reservations():
    """Create sample parking reservations"""
    print("\n📅 Creating Parking Reservations...")
    
    try:
        users = User_details.objects.all()[:5]
        parking_lots = ParkingLot.objects.all()[:3]
        
        reservation_count = 0
        for user in users:
            for i in range(2):  # 2 reservations per user
                lot = random.choice(parking_lots)
                available_spots = ParkingSpot.objects.filter(parking_lot=lot)[:5]
                spot = random.choice(available_spots) if available_spots.exists() else None
                
                reserved_from = timezone.now() + timedelta(days=random.randint(1, 30))
                reserved_until = reserved_from + timedelta(hours=random.randint(2, 8))
                
                reservation, created = ParkingReservation.objects.get_or_create(
                    user=user,
                    parking_lot=lot,
                    parking_spot=spot,
                    reserved_from=reserved_from,
                    reserved_until=reserved_until,
                    defaults={
                        'vehicle_type': random.choice(['car', 'bike', 'truck', 'van']),
                        'license_plate': f"{random.randint(1000, 9999)}-{random.choice(['A', 'B', 'C', 'D'])}",
                        'status': random.choice(['active', 'cancelled']),
                        'reservation_fee': Decimal(str(random.uniform(85.0, 425.0)))
                    }
                )
                if created:
                    reservation_count += 1
        
        print(f"✓ Created {reservation_count} reservations")
        return reservation_count
    
    except Exception as e:
        print(f"✗ Error creating reservations: {str(e)}")
        return 0


def create_sample_analytics():
    """Create daily parking analytics"""
    print("\n📊 Creating Parking Analytics...")
    
    try:
        parking_lots = ParkingLot.objects.all()
        
        analytics_count = 0
        for lot in parking_lots:
            # Create analytics for last 7 days
            for days_ago in range(1, 8):
                analytics_date = (timezone.now() - timedelta(days=days_ago)).date()
                
                analytics, created = ParkingAnalytics.objects.get_or_create(
                    parking_lot=lot,
                    date=analytics_date,
                    defaults={
                        'total_sessions': random.randint(50, 200),
                        'peak_occupancy_percent': random.randint(60, 95),
                        'average_duration_minutes': random.randint(90, 240),
                        'total_revenue': Decimal(str(random.uniform(42500, 170000))),
                        'peak_hour': random.randint(9, 17)
                    }
                )
                if created:
                    analytics_count += 1
        
        print(f"✓ Created {analytics_count} analytics records")
        return analytics_count
    
    except Exception as e:
        print(f"✗ Error creating analytics: {str(e)}")
        return 0


def create_pricing_rules():
    """Create pricing rules for parking lots"""
    print("\n💰 Creating Pricing Rules...")
    
    try:
        parking_lots = ParkingLot.objects.all()
        vehicle_types = ['car', 'truck', 'motorcycle', 'bus', 'unknown']
        
        rule_count = 0
        for lot in parking_lots:
            for vtype in vehicle_types:
                # Different rates for different vehicle types
                if vtype == 'truck':
                    base_rate = Decimal('5.00')
                elif vtype == 'motorcycle':
                    base_rate = Decimal('1.00')
                elif vtype == 'bus':
                    base_rate = Decimal('8.00')
                else:
                    base_rate = Decimal('2.50')
                
                rule, created = PricingRule.objects.get_or_create(
                    parking_lot=lot,
                    vehicle_type=vtype,
                    defaults={
                        'base_rate': base_rate,
                        'first_hour_free': random.choice([True, False]),
                        'max_daily_charge': Decimal(str(random.uniform(15, 50)))
                    }
                )
                if created:
                    rule_count += 1
        
        print(f"✓ Created {rule_count} pricing rules")
        return rule_count
    
    except Exception as e:
        print(f"✗ Error creating pricing rules: {str(e)}")
        return 0


def create_parking_lot_settings():
    """Create settings for each parking lot"""
    print("\n⚙️  Creating Parking Lot Settings...")
    
    try:
        parking_lots = ParkingLot.objects.all()
        
        settings_count = 0
        for lot in parking_lots:
            settings, created = ParkingLotSettings.objects.get_or_create(
                parking_lot=lot,
                defaults={
                    'latitude': round(random.uniform(28.0, 28.7), 4),
                    'longitude': round(random.uniform(77.0, 77.7), 4),
                    'address': f"{random.randint(100, 500)} {lot.lot_name} Street, New Delhi",
                    'phone': f"+91-{random.randint(6000000000, 9999999999)}",
                    'opening_time': '08:00',
                    'closing_time': '22:00',
                    'enable_reservations': True,
                    'enable_dynamic_pricing': random.choice([True, False]),
                    'enable_notifications': True,
                    'grace_period_minutes': random.choice([10, 15, 20]),
                    'hourly_rate': Decimal(str(round(random.uniform(2.0, 5.0), 2)))
                }
            )
            if created:
                settings_count += 1
        
        print(f"✓ Created {settings_count} parking lot settings")
        return settings_count
    
    except Exception as e:
        print(f"✗ Error creating settings: {str(e)}")
        return 0


def main():
    print("=" * 70)
    print("SMARTSLOT - COMPLETE ANALYTICS DATA POPULATION")
    print("=" * 70)
    
    try:
        # Check if data already exists
        existing_users = User_details.objects.count()
        if existing_users == 0:
            print("\n⚠️  No users found. Please create users first!")
            return
        
        # Verify parking lots exist
        parking_lots = ParkingLot.objects.count()
        if parking_lots == 0:
            print("⚠️  No parking lots found. Please run quick_sample_data.py first!")
            return
        
        print(f"\n✓ Found {existing_users} users and {parking_lots} parking lots")
        
        # Create all data
        results = {
            'notifications': create_sample_notifications(),
            'payments': create_sample_payments(),
            'reservations': create_sample_reservations(),
            'analytics': create_sample_analytics(),
            'pricing_rules': create_pricing_rules(),
            'settings': create_parking_lot_settings()
        }
        
        # Print summary
        print("\n" + "=" * 70)
        print("✅ ANALYTICS DATA POPULATION COMPLETE!")
        print("=" * 70)
        
        print("\n📈 Summary:")
        print(f"  • Notifications Created: {results['notifications']}")
        print(f"  • Payment Records: {results['payments']}")
        print(f"  • Reservations: {results['reservations']}")
        print(f"  • Analytics Records: {results['analytics']}")
        print(f"  • Pricing Rules: {results['pricing_rules']}")
        print(f"  • Lot Settings: {results['settings']}")
        
        total = sum(results.values())
        print(f"\n  • Total Records Created: {total}")
        
        # Display database counts
        print("\n📊 Database Summary:")
        print(f"  • Total Notifications: {UserNotification.objects.count()}")
        print(f"  • Total Payments: {Payment.objects.count()}")
        print(f"  • Total Reservations: {ParkingReservation.objects.count()}")
        print(f"  • Total Analytics Records: {ParkingAnalytics.objects.count()}")
        print(f"  • Pricing Rules: {PricingRule.objects.count()}")
        print(f"  • Lot Settings: {ParkingLotSettings.objects.count()}")
        
        print("\n" + "=" * 70)
        print("All analytics and notification systems are now ready for testing!")
        print("=" * 70)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
