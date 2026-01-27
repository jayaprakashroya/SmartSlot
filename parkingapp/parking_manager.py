"""
Parking Management System
Handles vehicle detection, spot assignment, and customer queries
"""

from django.utils import timezone
from .models import Vehicle, ParkedVehicle, ParkingSpot, ParkingLot
from django.db.models import Q
import logging

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
            for spot in parking_lot.spots.all():
                parked = parked_vehicle = spot.get_current_vehicle()
                spot_details.append({
                    'spot_number': spot.spot_number,
                    'spot_type': spot.get_spot_type_display(),
                    'is_occupied': spot.is_occupied(),
                    'vehicle_plate': parked_vehicle.vehicle.license_plate if parked_vehicle else None,
                    'vehicle_owner': parked_vehicle.vehicle.owner_name if parked_vehicle else None,
                    'parked_since': parked_vehicle.checkin_time if parked_vehicle else None,
                })
            
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
