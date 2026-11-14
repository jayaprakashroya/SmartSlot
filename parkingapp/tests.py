from django.test import TestCase
from django.utils import timezone

from .models import (
    Vehicle, ParkingLot, ParkingSpot, ParkedVehicle,
    ParkingHistory, DisputeLog,
    DetectionLog, PendingSyncQueue, AdminAction
)
from .edge_case_handlers import VehicleSearchHandler
import json


class SearchHandlerTests(TestCase):
    def setUp(self):
        # set up common objects for tests
        self.lot = ParkingLot.objects.create(lot_name='Test Lot', total_spots=10)
        self.spot = ParkingSpot.objects.create(
            parking_lot=self.lot,
            spot_number='A1',
            x_position=0,
            y_position=0
        )
        self.vehicle = Vehicle.objects.create(
            license_plate='TEST123',
            vehicle_type='car'
        )
        # create parked vehicle record
        self.parked = ParkedVehicle.objects.create(
            vehicle=self.vehicle,
            parking_spot=self.spot,
            parking_lot=self.lot
        )
        # create history entry
        self.history = ParkingHistory.objects.create(
            phone_number='+10000000000',
            parked_vehicle=self.parked,
            ticket_id='T1234'
        )
        # create a staff admin user for view tests
        from django.contrib.auth.models import User
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.client.force_login(self.admin_user)

    def test_search_by_phone_returns_record(self):
        results = VehicleSearchHandler.search_by_phone('+10000000000')
        # should have current parking info
        self.assertIsNotNone(results['current'])
        # license plate returned should be masked (first and last char visible)
        self.assertTrue(results['current']['license_plate'].startswith('T'))
        self.assertTrue(results['current']['license_plate'].endswith('3'))
        # recent list should be empty since current is active
        self.assertEqual(results['recent'], [])

    def test_get_spot_history_includes_disputes(self):
        # add a dispute for this parked vehicle
        DisputeLog.objects.create(
            parked_vehicle=self.parked,
            customer_name='John',
            customer_phone='+10000000000',
            dispute_type='other',
            description='Test'
        )
        from .edge_case_handlers import DisputeHandler
        # call the helper directly via get_spot_history
        history = DisputeHandler.get_spot_history(self.spot.spot_id)
        self.assertTrue(len(history) >= 1)
        self.assertEqual(history[0]['disputes'], 1)

    # ---------- fallback behavior tests ----------
    def test_search_by_phone_with_no_data_returns_sample(self):
        # clear history table
        ParkingHistory.objects.all().delete()
        results = VehicleSearchHandler.search_by_phone('+9999999999')
        self.assertIsNotNone(results['current'])
        self.assertIn('Demo Lot', results['current']['parking_lot'])

    def test_api_admin_search_vehicle_fallback(self):
        # ensure no parked vehicles
        ParkedVehicle.objects.all().delete()
        response = self.client.post(
            '/api/admin/search-vehicle/',
            data=json.dumps({'search': 'XYZ', 'type': 'vehicle_number'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 1)
        self.assertEqual(data['vehicles'][0]['vehicle_number'], 'SAMPLE1234')

    def test_parking_history_api_fallback(self):
        ParkingHistory.objects.all().delete()
        response = self.client.get('/api/parking-history/?phone=+0000000000')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['current_parking']['license_plate'], 'SAMPLE1234')

    def test_check_double_parking_fallback(self):
        # ensure no detection logs
        DetectionLog.objects.all().delete()
        response = self.client.post('/api/check-double-parking/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['double_parked_count'], 1)
        self.assertEqual(data['spots'][0]['spot_number'], 'A1')

    def test_pending_sync_queue_view_fallback(self):
        PendingSyncQueue.objects.all().delete()
        response = self.client.get('/offline-mode/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sample data', response.content.decode())

    def test_low_confidence_detections_fallback(self):
        DetectionLog.objects.all().delete()
        response = self.client.get('/low-confidence-detections/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sample low confidence detection', response.content.decode())

    def test_plate_access_logs_fallback(self):
        AdminAction.objects.all().delete()
        response = self.client.get('/plate-access-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('sample entry', response.content.decode().lower())

    def test_admin_dashboard_disputes_fallback(self):
        DisputeLog.objects.all().delete()
        response = self.client.get('/admin-dashboard/disputes/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sample dispute', response.content.decode())

    def test_admin_action_history_fallback(self):
        AdminAction.objects.all().delete()
        response = self.client.get('/admin-action-history/')
        self.assertEqual(response.status_code, 200)
        # view access will auto-log at least one entry; ensure page renders without errors
        self.assertIn('Admin:', response.content.decode())

    def test_admin_dashboard_disputes_fallback(self):
        DisputeLog.objects.all().delete()
        response = self.client.get('/admin-dashboard/disputes/')
        self.assertEqual(response.status_code, 200)
        # sample dispute row should show sample plate
        self.assertIn('SAMPLE1234', response.content.decode())
