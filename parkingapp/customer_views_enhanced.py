"""
Enhanced Find My Car - Real-Time License Plate Tracking
Shows customers exactly which parking spot their car is in with visual map
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .parking_spot_tracker import ParkingSpotTracker
from .parking_manager import ParkingManager
from .models import ParkedVehicle, ParkingSpot, Vehicle, AdminAction
import json
import logging
import pickle
import os

logger = logging.getLogger(__name__)

# Helper function
def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'Unknown')
    return ip

# Global tracker instance
_parking_tracker = None

def get_parking_tracker():
    """Get or initialize the parking tracker."""
    global _parking_tracker
    
    if _parking_tracker is None:
        try:
            # Load parking positions
            pos_file = 'parkingapp/CarParkPos'
            if os.path.exists(pos_file):
                with open(pos_file, 'rb') as f:
                    parking_positions = pickle.load(f)
                    _parking_tracker = ParkingSpotTracker(parking_positions, 1280, 720)
                    logger.info(f"Parking tracker initialized with {len(parking_positions)} spots")
        except Exception as e:
            logger.error(f"Failed to initialize parking tracker: {e}")
    
    return _parking_tracker


def find_my_car_enhanced(request):
    """
    Enhanced Find My Car page with real-time tracking
    Shows visual map of parking lot with vehicle locations
    """
    context = {
        'page_title': 'Find My Car - Real-Time Tracking',
        'search_results': None,
        'parking_status': None,
        'error_message': None,
    }
    
    tracker = get_parking_tracker()
    
    if not tracker:
        context['error_message'] = '❌ Parking tracking system is not available. Please try again later.'
        return render(request, 'find_my_car_enhanced.html', context)
    
    # Get current parking lot status
    try:
        context['parking_status'] = tracker.get_parking_status()
    except Exception as e:
        logger.error(f"Error getting parking status: {e}")
        context['error_message'] = 'Error retrieving parking status'
    
    if request.method == 'POST':
        license_plate = request.POST.get('license_plate', '').strip().upper()
        
        if not license_plate:
            context['error_message'] = '⚠️ Please enter a license plate number'
        else:
            try:
                # Search for vehicle
                result = tracker.find_vehicle_spot(license_plate)
                
                if result:
                    context['search_results'] = {
                        'found': True,
                        'plate': result['plate'],
                        'spot_number': result['spot_number'],
                        'position': result['position'],
                        'x': result['position'][0],
                        'y': result['position'][1],
                        'parked_at': result['parked_at'],
                        'confidence': f"{result['confidence']*100:.0f}%",
                        'message': f"✅ Found your car! It's parked at Spot #{result['spot_number']}"
                    }
                    
                    # Also get parking history
                    history = tracker.get_vehicle_history(license_plate)
                    if history:
                        context['search_results']['history'] = history
                
                else:
                    # Try ParkingManager as fallback
                    try:
                        vehicle_location = ParkingManager.find_vehicle_location(license_plate)
                        if vehicle_location:
                            context['search_results'] = {
                                'found': True,
                                'plate': license_plate,
                                'spot_number': vehicle_location.get('spot_number', 'Unknown'),
                                'lot_name': vehicle_location.get('lot_name', 'N/A'),
                                'message': f"✅ Found your car at {vehicle_location.get('lot_name')}!"
                            }
                        else:
                            context['search_results'] = {
                                'found': False,
                                'plate': license_plate,
                                'message': f"❌ Car with plate '{license_plate}' not found in parking lot"
                            }
                    except Exception as e:
                        logger.warning(f"ParkingManager lookup failed: {e}")
                        context['search_results'] = {
                            'found': False,
                            'plate': license_plate,
                            'message': f"❌ Car '{license_plate}' is not currently parked"
                        }
            
            except Exception as e:
                logger.error(f"Error searching for vehicle: {e}")
                context['error_message'] = f'Error searching for vehicle: {str(e)}'
    
    return render(request, 'find_my_car_enhanced.html', context)


@require_http_methods(["GET"])
def api_parking_status_realtime(request):
    """
    API endpoint for real-time parking lot status
    Returns JSON with all parking spaces and occupancy
    """
    tracker = get_parking_tracker()
    
    if not tracker:
        return JsonResponse({
            'success': False,
            'error': 'Parking tracker not available'
        }, status=503)
    
    try:
        status = tracker.get_parking_status()
        return JsonResponse({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"Error in api_parking_status_realtime: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def api_find_vehicle_realtime(request):
    """
    API endpoint to find a specific vehicle
    Users can only search their own vehicles, admins can search all
    POST data: {license_plate: "ABC-1234"}
    """
    tracker = get_parking_tracker()
    
    if not tracker:
        return JsonResponse({
            'success': False,
            'error': 'Parking tracker not available'
        }, status=503)
    
    try:
        data = json.loads(request.body)
        license_plate = data.get('license_plate', '').strip().upper()
        
        if not license_plate:
            return JsonResponse({
                'success': False,
                'error': 'License plate is required'
            }, status=400)
        
        # Authorization check - users can only search their own vehicles
        try:
            vehicle = Vehicle.objects.get(license_plate=license_plate)
            if not (request.user.is_staff or request.user.is_superuser):
                # Regular users can only search for their own vehicles
                try:
                    ParkedVehicle.objects.get(vehicle=vehicle, user=request.user)
                except ParkedVehicle.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': "You can only search your own vehicles"
                    }, status=403)
        except Vehicle.DoesNotExist:
            pass  # Continue with search anyway
        
        result = tracker.find_vehicle_spot(license_plate)
        
        if result:
            return JsonResponse({
                'success': True,
                'vehicle_found': True,
                'data': result
            })
        else:
            return JsonResponse({
                'success': True,
                'vehicle_found': False,
                'message': f'Vehicle {license_plate} not found'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_find_vehicle_realtime: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def api_update_parking_spot(request):
    """
    API endpoint to update parking spot with detected vehicle - ADMIN ONLY
    Called by YOLOv8 detection system
    
    POST data: {
        license_plate: "ABC-1234",
        spot_id: 5,
        bbox: [100, 100, 200, 150],
        confidence: 0.95
    }
    """
    tracker = get_parking_tracker()
    
    if not tracker:
        return JsonResponse({
            'success': False,
            'error': 'Parking tracker not available'
        }, status=503)
    
    try:
        data = json.loads(request.body)
        license_plate = data.get('license_plate', '').strip().upper()
        bbox = data.get('bbox', [0, 0, 100, 100])
        confidence = data.get('confidence', 0.8)
        
        if not license_plate:
            return JsonResponse({
                'success': False,
                'error': 'License plate is required'
            }, status=400)
        
        # Assign vehicle to parking spot
        result = tracker.assign_vehicle_to_spot(license_plate, tuple(bbox), confidence)
        
        return JsonResponse({
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'data': {
                'plate': result.get('plate'),
                'spot_id': result.get('spot_id'),
                'spot_number': result.get('spot_id', -1) + 1 if result.get('spot_id', -1) >= 0 else None,
                'position': result.get('position'),
                'overlap': result.get('overlap')
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_update_parking_spot: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def api_remove_vehicle(request):
    """
    API endpoint to remove vehicle from parking spot - ADMIN ONLY - DESTRUCTIVE
    POST data: {license_plate: "ABC-1234"}
    """
    tracker = get_parking_tracker()
    
    if not tracker:
        return JsonResponse({
            'success': False,
            'error': 'Parking tracker not available'
        }, status=503)
    
    try:
        data = json.loads(request.body)
        license_plate = data.get('license_plate', '').strip().upper()
        
        # Log admin action
        try:
            vehicle = Vehicle.objects.get(license_plate=license_plate)
            AdminAction.objects.create(
                admin=request.user,
                action='REMOVE_VEHICLE',
                details=f'Removed vehicle {license_plate} from system',
                ip_address=get_client_ip(request),
                timestamp=timezone.now(),
                reason=data.get('reason', 'Not specified'),
                is_critical=True
            )
        except:
            pass  # Continue even if logging fails
        

        
        if not license_plate:
            return JsonResponse({
                'success': False,
                'error': 'License plate is required'
            }, status=400)
        
        # Find and remove the vehicle
        removed_spot = None
        for spot_id, spot_data in tracker.spot_assignments.items():
            if spot_data and spot_data['plate'].upper() == license_plate:
                del tracker.spot_assignments[spot_id]
                tracker.spot_occupancy[spot_id] = False
                removed_spot = spot_id + 1
                break
        
        if removed_spot:
            return JsonResponse({
                'success': True,
                'message': f'Vehicle {license_plate} removed from Spot #{removed_spot}',
                'spot_number': removed_spot
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Vehicle {license_plate} not found in any parking spot'
            }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in api_remove_vehicle: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
