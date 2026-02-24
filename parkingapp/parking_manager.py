"""
Parking Management System
Handles vehicle detection, spot assignment, and customer queries
"""

from django.utils import timezone
from .models import Vehicle, ParkedVehicle, ParkingSpot, ParkingLot
from django.db.models import Q
from django.conf import settings
import random
import logging

# sample vehicle data used when randomizing occupancy
_SAMPLE_VEHICLES = [
    {'plate': 'ABC1234', 'owner': 'John Doe'},
    {'plate': 'XYZ9876', 'owner': 'Jane Smith'},
    {'plate': 'MH12DE1432', 'owner': 'Ravi Kumar'},
    {'plate': 'DL8CAF1234', 'owner': 'Priya Singh'},
    {'plate': 'KA05MN6789', 'owner': 'Ajay Sharma'},
    {'plate': 'TN09WX4567', 'owner': 'Sunita Patel'},
    {'plate': 'GJ01PQ2345', 'owner': 'Arun Mehta'},
    {'plate': 'UP32ZZ9999', 'owner': 'Neha Verma'},
]

logger = logging.getLogger(__name__)


class ParkingManager:
    """Manage parking operations"""
    
    @staticmethod
    def register_vehicle(license_plate, vehicle_type='car', owner_name=None, owner_phone=None, color=None):
        """Register or get a vehicle"""
        vehicle, created = Vehicle.objects.get_or_create(
            license_plate=license_plate.upper(),
            defaults={
                'vehicle_type': vehicle_type,
                'owner_name': owner_name,
                'owner_phone': owner_phone,
                'color': color
            }
        )
        return vehicle, created
    
    @staticmethod
    def find_available_spot(parking_lot, spot_type='regular'):
        """Find an available parking spot"""
        available_spot = ParkingSpot.objects.filter(
            parking_lot=parking_lot,
            spot_type=spot_type
        ).exclude(
            parkedvehicle__checkout_time__isnull=True  # Exclude occupied spots
        ).first()
        return available_spot
    
    @staticmethod
    def checkin_vehicle(license_plate, parking_lot, parking_spot=None, vehicle_type='car', 
                       owner_name=None, owner_phone=None, color=None, entry_image_path=None):
        """
        Check in a vehicle to a parking spot
        
        Args:
            license_plate: Vehicle license plate
            parking_lot: ParkingLot instance
            parking_spot: ParkingSpot instance (auto-assigned if None)
            vehicle_type: Type of vehicle
            owner_name: Name of vehicle owner
            owner_phone: Phone number of owner
            color: Vehicle color
            entry_image_path: Path to entry image
        
        Returns:
            ParkedVehicle instance or None
        """
        try:
            # Register vehicle if not already registered
            vehicle, _ = ParkingManager.register_vehicle(
                license_plate, 
                vehicle_type=vehicle_type,
                owner_name=owner_name,
                owner_phone=owner_phone,
                color=color
            )
            
            # Check if vehicle is already parked
            existing_parked = ParkedVehicle.objects.filter(
                vehicle=vehicle,
                checkout_time__isnull=True
            ).first()
            
            if existing_parked:
                logger.warning(f"Vehicle {license_plate} is already parked at {existing_parked.parking_spot}")
                return existing_parked
            
            # Auto-assign spot if not provided
            if parking_spot is None:
                parking_spot = ParkingManager.find_available_spot(parking_lot)
            
            if parking_spot is None:
                logger.error(f"No available parking spots in {parking_lot}")
                return None
            
            # Create parking record
            parked_vehicle = ParkedVehicle.objects.create(
                vehicle=vehicle,
                parking_spot=parking_spot,
                parking_lot=parking_lot,
                entry_image_path=entry_image_path,
                notes=f"Auto-assigned to {parking_spot.spot_number}"
            )
            
            logger.info(f"Vehicle {license_plate} checked in at {parking_spot.spot_number}")
            return parked_vehicle
        
        except Exception as e:
            logger.error(f"Error during vehicle check-in: {e}")
            return None
    
    @staticmethod
    def checkout_vehicle(license_plate, exit_image_path=None):
        """
        Check out a vehicle from parking
        
        Args:
            license_plate: Vehicle license plate
            exit_image_path: Path to exit image
        
        Returns:
            ParkedVehicle instance or None
        """
        try:
            vehicle = Vehicle.objects.filter(license_plate=license_plate.upper()).first()
            if not vehicle:
                logger.error(f"Vehicle {license_plate} not found")
                return None
            
            parked_vehicle = ParkedVehicle.objects.filter(
                vehicle=vehicle,
                checkout_time__isnull=True
            ).first()
            
            if not parked_vehicle:
                logger.error(f"Vehicle {license_plate} not currently parked")
                return None
            
            parked_vehicle.exit_image_path = exit_image_path
            parked_vehicle.checkout()
            
            logger.info(f"Vehicle {license_plate} checked out from {parked_vehicle.parking_spot.spot_number}")
            return parked_vehicle
        
        except Exception as e:
            logger.error(f"Error during vehicle check-out: {e}")
            return None
    
    @staticmethod
    def find_vehicle_location(license_plate):
        """
        Find where a vehicle is currently parked
        
        Args:
            license_plate: Vehicle license plate
        
        Returns:
            Dictionary with location info or None
        """
        try:
            vehicle = Vehicle.objects.filter(license_plate=license_plate.upper()).first()
            if not vehicle:
                return None
            
            parked_vehicle = ParkedVehicle.objects.filter(
                vehicle=vehicle,
                checkout_time__isnull=True
            ).first()
            
            if not parked_vehicle:
                return None
            
            parking_spot = parked_vehicle.parking_spot
            if not parking_spot:
                return None
            
            return {
                'license_plate': vehicle.license_plate,
                'vehicle_type': vehicle.get_vehicle_type_display(),
                'owner_name': vehicle.owner_name or 'Not registered',
                'parking_lot': parking_spot.parking_lot.lot_name,
                'spot_number': parking_spot.spot_number,
                'spot_type': parking_spot.get_spot_type_display(),
                'checkin_time': parked_vehicle.checkin_time,
                'duration': parked_vehicle.get_duration_display(),
                'x_position': parking_spot.x_position,
                'y_position': parking_spot.y_position,
                'status': 'parked'
            }
        
        except Exception as e:
            logger.error(f"Error finding vehicle location: {e}")
            return None
    
    @staticmethod
    def get_parking_lot_status(parking_lot):
        """
        Get current status of parking lot
        
        Args:
            parking_lot: ParkingLot instance
        
        Returns:
            Dictionary with parking lot info
        """
        try:
            total_spots = parking_lot.total_spots
            occupied_count = ParkedVehicle.objects.filter(
                parking_lot=parking_lot,
                checkout_time__isnull=True
            ).count()
            
            available_count = total_spots - occupied_count
            occupancy_rate = (occupied_count / total_spots * 100) if total_spots > 0 else 0

            # Get spot details
            spot_details = []
            spots_qs = ParkingSpot.objects.filter(parking_lot=parking_lot)
            for spot in spots_qs:
                parked_vehicle = ParkedVehicle.objects.filter(parking_spot=spot, checkout_time__isnull=True).first()
                spot_details.append({
                    'spot_id': spot.spot_id,
                    'spot_number': spot.spot_number,
                    'spot_type': getattr(spot, 'spot_type', 'Regular'),
                    'is_occupied': bool(parked_vehicle),
                    'vehicle_plate': parked_vehicle.vehicle.license_plate if parked_vehicle else None,
                    'vehicle_owner': parked_vehicle.vehicle.owner_name if parked_vehicle else None,
                    'parked_since': parked_vehicle.checkin_time if parked_vehicle else None,
                })
            
            # if no actual spots are configured, provide example rows for demo purposes
            if not spot_details:
                spot_details = [
                    {'spot_id': 1, 'spot_number': 'A1', 'spot_type': 'Regular', 'is_occupied': False, 'vehicle_plate': None, 'vehicle_owner': None, 'parked_since': None},
                    {'spot_id': 2, 'spot_number': 'A2', 'spot_type': 'Regular', 'is_occupied': True,  'vehicle_plate': 'ABC1234', 'vehicle_owner': 'John Doe', 'parked_since': timezone.now()},
                    {'spot_id': 3, 'spot_number': 'B1', 'spot_type': 'Reserved', 'is_occupied': False, 'vehicle_plate': None, 'vehicle_owner': None, 'parked_since': None},
                    {'spot_id': 4, 'spot_number': 'B2', 'spot_type': 'Regular', 'is_occupied': True,  'vehicle_plate': 'XYZ9876', 'vehicle_owner': 'Jane Smith', 'parked_since': timezone.now()},
                    {'spot_id': 5, 'spot_number': 'C1', 'spot_type': 'Handicapped', 'is_occupied': False, 'vehicle_plate': None, 'vehicle_owner': None, 'parked_since': None},
                    {'spot_id': 6, 'spot_number': 'C2', 'spot_type': 'Regular', 'is_occupied': True,  'vehicle_plate': 'MH12DE1432', 'vehicle_owner': 'Ravi Kumar', 'parked_since': timezone.now()},
                    {'spot_id': 7, 'spot_number': 'D1', 'spot_type': 'Regular', 'is_occupied': False, 'vehicle_plate': None, 'vehicle_owner': None, 'parked_since': None},
                    {'spot_id': 8, 'spot_number': 'D2', 'spot_type': 'Reserved', 'is_occupied': True,  'vehicle_plate': 'DL8CAF1234', 'vehicle_owner': 'Priya Singh', 'parked_since': timezone.now()},
                ]
                # when randomization is enabled, assign random sample vehicles to demo spots
                if settings.RANDOMIZE_OCCUPANCY:
                    for spot in spot_details:
                        if spot['is_occupied']:
                            sample = random.choice(_SAMPLE_VEHICLES)
                            spot['vehicle_plate'] = sample['plate']
                            spot['vehicle_owner'] = sample['owner']
                            spot['parked_since'] = timezone.now()

            # apply randomization if requested in settings (testing/demo mode)
            if settings.RANDOMIZE_OCCUPANCY and total_spots > 0:
                # choose a percentage within configured bounds
                perc = random.uniform(settings.OCCUPANCY_RANDOM_MIN_PERCENT,
                                      settings.OCCUPANCY_RANDOM_MAX_PERCENT)
                occupied_count = int(round(total_spots * perc / 100))
                available_count = total_spots - occupied_count
                occupancy_rate = round((occupied_count / total_spots * 100), 2)

                # shuffle spot details and mark the first N as occupied
                if spot_details:
                    random.shuffle(spot_details)
                    for idx, spot in enumerate(spot_details):
                        spot['is_occupied'] = idx < occupied_count
                        if spot['is_occupied']:
                            # assign a random sample vehicle for demos
                            sample = random.choice(_SAMPLE_VEHICLES)
                            spot['vehicle_plate'] = sample['plate']
                            spot['vehicle_owner'] = sample['owner']
                            spot['parked_since'] = timezone.now()
                        else:
                            spot['vehicle_plate'] = None
                            spot['vehicle_owner'] = None
                            spot['parked_since'] = None

            return {
                'lot_name': parking_lot.lot_name,
                'total_spots': total_spots,
                'occupied_spots': occupied_count,
                'available_spots': available_count,
                'occupancy_rate': round(occupancy_rate, 2),
                'spots': spot_details
            }
        
        except Exception as e:
            logger.error(f"Error getting parking lot status: {e}")
            return None
    
    @staticmethod
    def update_vehicle_detection_from_yolov8(parking_lot, detections, parking_spots_map):
        """
        Update parking status based on YOLOv8 detections
        
        Args:
            parking_lot: ParkingLot instance
            detections: List of detected vehicles (from YOLOv8)
            parking_spots_map: Dict mapping spot positions to ParkingSpot instances
        """
        try:
            # First, checkout all vehicles not in current detection
            current_plates = {det.get('license_plate') for det in detections if det.get('license_plate')}
            
            # Mark vehicles as checked out if not detected
            active_vehicles = ParkedVehicle.objects.filter(
                parking_lot=parking_lot,
                checkout_time__isnull=True
            )
            
            for parked in active_vehicles:
                if parked.vehicle.license_plate not in current_plates:
                    parked.checkout()
            
            # Checkin new vehicles
            for detection in detections:
                license_plate = detection.get('license_plate')
                if not license_plate:
                    continue
                
                # Skip if already parked
                if ParkedVehicle.objects.filter(
                    vehicle__license_plate=license_plate.upper(),
                    checkout_time__isnull=True
                ).exists():
                    continue
                
                # Find parking spot for this detection
                parking_spot = parking_spots_map.get(detection.get('spot_id'))
                
                ParkingManager.checkin_vehicle(
                    license_plate,
                    parking_lot,
                    parking_spot=parking_spot,
                    vehicle_type=detection.get('vehicle_type', 'car'),
                    color=detection.get('color')
                )
        
        except Exception as e:
            logger.error(f"Error updating vehicle detection: {e}")
    
    @staticmethod
    def get_recent_activity(parking_lot, hours=24):
        """Get recent parking activity"""
        from datetime import timedelta
        
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        activity = ParkedVehicle.objects.filter(
            parking_lot=parking_lot,
            checkin_time__gte=time_threshold
        ).select_related('vehicle', 'parking_spot').order_by('-checkin_time')
        
        return activity
    
    @staticmethod
    def get_parking_statistics(parking_lot, days=7):
        """Get parking statistics for specified period"""
        from datetime import timedelta
        
        time_threshold = timezone.now() - timedelta(days=days)
        
        total_vehicles = ParkedVehicle.objects.filter(
            parking_lot=parking_lot,
            checkin_time__gte=time_threshold
        ).values('vehicle').distinct().count()
        
        total_sessions = ParkedVehicle.objects.filter(
            parking_lot=parking_lot,
            checkin_time__gte=time_threshold
        ).count()
        
        avg_duration_minutes = ParkedVehicle.objects.filter(
            parking_lot=parking_lot,
            checkin_time__gte=time_threshold,
            checkout_time__isnull=False
        ).values_list('duration_minutes', flat=True)
        
        avg_duration = sum(avg_duration_minutes) / len(avg_duration_minutes) if avg_duration_minutes else 0
        
        return {
            'period_days': days,
            'total_unique_vehicles': total_vehicles,
            'total_parking_sessions': total_sessions,
            'average_duration_minutes': round(avg_duration, 2),
            'average_duration_hours': round(avg_duration / 60, 2)
        }
