import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.test import Client
from parkingapp.models import User_details, ParkingLot, ParkingReservation

client = Client()

# utility to login/create demo user

def ensure_logged_in():
    # create or get a user in custom table
    user, _ = User_details.objects.get_or_create(Email='test@example.com', defaults={'Password':'dummy'})
    session = client.session
    session['user_email'] = user.Email
    session['user_id'] = user.User_id
    session.save()
    return user

# create parking lot if not exists
def ensure_lot():
    lot, _ = ParkingLot.objects.get_or_create(lot_name='Test Lot', defaults={'total_spots':50})
    return lot


def test_from_date_in_past():
    ensure_logged_in()
    lot = ensure_lot()
    past = timezone.now() - timedelta(days=1)
    future = timezone.now() + timedelta(hours=1)
    resp = client.post('/reserve-parking/', {
        'parking_lot': lot.lot_id,
        'reserved_from': past.isoformat(),
        'reserved_until': future.isoformat(),
        'vehicle_type': 'car'
    })
    assert b'Cannot reserve for past dates' in resp.content


def test_from_date_not_15_minutes_ahead():
    ensure_logged_in()
    lot = ensure_lot()
    now = timezone.now()
    start = now + timedelta(minutes=5)
    end = now + timedelta(hours=1)
    resp = client.post('/reserve-parking/', {
        'parking_lot': lot.lot_id,
        'reserved_from': start.isoformat(),
        'reserved_until': end.isoformat(),
        'vehicle_type': 'car'
    })
    assert b'Start time must be at least 15 minutes from now' in resp.content


def test_to_before_from():
    ensure_logged_in()
    lot = ensure_lot()
    now = timezone.now() + timedelta(hours=2)
    start = now + timedelta(hours=1)
    end = now
    resp = client.post('/reserve-parking/', {
        'parking_lot': lot.lot_id,
        'reserved_from': start.isoformat(),
        'reserved_until': end.isoformat(),
        'vehicle_type': 'car'
    })
    assert b'End time must be after start time' in resp.content


def test_valid_reservation_creates():
    ensure_logged_in()
    lot = ensure_lot()
    now = timezone.now()
    start = now + timedelta(hours=1)
    end = now + timedelta(hours=2)
    resp = client.post('/reserve-parking/', {
        'parking_lot': lot.lot_id,
        'reserved_from': start.isoformat(),
        'reserved_until': end.isoformat(),
        'vehicle_type': 'car'
    })
    # should redirect to my_reservations
    assert resp.status_code in (302, 301)
    # confirm reservation created
    res = ParkingReservation.objects.filter(parking_lot=lot, reserved_from__gte=start - timedelta(seconds=1)).first()
    assert res is not None


if __name__ == '__main__':
    print("Running reservation validation tests...")
    test_from_date_in_past()
    test_from_date_not_15_minutes_ahead()
    test_to_before_from()
    test_valid_reservation_creates()
    print("All reservation tests passed!")
