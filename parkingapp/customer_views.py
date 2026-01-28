"""
Customer-facing views for finding parked vehicles
Integrated with YOLOv8 vehicle detection and license plate recognition
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ParkingLot, Vehicle, ParkedVehicle, ParkingSpot
from .parking_manager import ParkingManager
from .yolov8_detector import (
    VehicleDetector,
    LicensePlateOCR,
    ParkingSpotTracker,
    ParkingVideoProcessor,
)
import json
import logging
import os
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Initialize YOLOv8 components
try:
    VEHICLE_DETECTOR = VehicleDetector(model_name="yolov8n.pt")
    LICENSE_PLATE_OCR = LicensePlateOCR()
    YOLOV8_ENABLED = True
    logger.info("YOLOv8 components initialized successfully")
except Exception as e:
    logger.warning(f"YOLOv8 initialization failed: {e}")
    YOLOV8_ENABLED = False


def find_my_car(request):
    """
    Customer page to find their parked vehicle
    Allows search by license plate
    """
    vehicle_found = None
    search_attempted = False
    searched_plate = ""
    
    if request.method == 'POST':
        license_plate = request.POST.get('license_plate', '').strip().upper()
        search_attempted = True
        searched_plate = license_plate
        
        if not license_plate:
            messages.error(request, 'Please enter a license plate number.')
        else:
            vehicle_found = ParkingManager.find_vehicle_location(license_plate)
            
            if not vehicle_found:
                messages.error(request, f'Vehicle with plate "{license_plate}" is not currently parked or not found.')
            else:
                messages.success(request, f'Found your vehicle! It is parked at Spot {vehicle_found["spot_number"]} in {vehicle_found["parking_lot"]}')
    
    context = {
        'vehicle_found': vehicle_found,
        'search_attempted': search_attempted,
        'searched_plate': searched_plate
    }
    return render(request, 'find_my_car.html', context)


@login_required
def parking_lot_status(request, lot_id=None):
    """
    Display current status of parking lot
    Shows all occupied and available spots
    """
    try:
        if lot_id:
            parking_lot = ParkingLot.objects.get(lot_id=lot_id)
        else:
            # Get first parking lot or default
            parking_lot = ParkingLot.objects.first()
            if not parking_lot:
                messages.error(request, 'No parking lot configured.')
                return render(request, 'parking_lot_status.html', {'lot_status': None})
        
        status = ParkingManager.get_parking_lot_status(parking_lot)
        all_lots = ParkingLot.objects.all()
        
        context = {
            'status': status,
            'lot': parking_lot,
            'all_lots': all_lots,
            'current_lot_id': parking_lot.lot_id
        }
        return render(request, 'parking_lot_status.html', context)
    
    except ParkingLot.DoesNotExist:
        messages.error(request, 'Parking lot not found.')
        return render(request, 'parking_lot_status.html', {'lot_status': None})


@login_required
def parking_lot_status_all_lots(request):
    """
    Display status of ALL parking lots on one page
    Shows occupancy for each lot with quick access to heatmaps
    """
    try:
        all_lots = ParkingLot.objects.all().order_by('lot_name')
        
        # Calculate statistics for each lot
        parking_lots = []
        total_occupied = 0
        total_available = 0
        total_spots = 0
        
        for lot in all_lots:
            status = ParkingManager.get_parking_lot_status(lot)
            
            lot_data = {
                'lot_id': lot.lot_id,
                'lot_name': lot.lot_name,
                'total_spots': status.get('total_spots', 0),
                'occupied_spots': status.get('parked_vehicles_count', 0),
                'available_spots': status.get('available_spaces_count', 0),
                'occupancy_rate': status.get('occupancy_percentage', 0)
            }
            
            parking_lots.append(lot_data)
            total_occupied += lot_data['occupied_spots']
            total_available += lot_data['available_spots']
            total_spots += lot_data['total_spots']
        
        # Calculate overall occupancy rate
        overall_rate = 0
        if total_spots > 0:
            overall_rate = round((total_occupied / total_spots) * 100, 1)
        
        total_stats = {
            'total': total_spots,
            'occupied': total_occupied,
            'available': total_available,
            'occupancy_rate': overall_rate
        }
        
        context = {
            'parking_lots': parking_lots,
            'total_stats': total_stats
        }
        
        return render(request, 'parkingapp/parking_status_all_lots.html', context)
    
    except Exception as e:
        logger.error(f"Error in parking_lot_status_all_lots: {e}")
        messages.error(request, 'Error loading parking lot status')
        return render(request, 'parkingapp/parking_status_all_lots.html', {
            'parking_lots': [],
            'total_stats': {'total': 0, 'occupied': 0, 'available': 0, 'occupancy_rate': 0}
        })


def vehicle_history(request):
    """
    Display parking history for a specific vehicle
    """
    parking_records = []
    search_attempted = False
    total_sessions = 0
    active_sessions = 0
    total_hours = 0
    total_fees = 0
    search_query = ""
    
    if request.method == 'POST' or request.GET.get('search'):
        license_plate = request.POST.get('license_plate', '') or request.GET.get('search', '')
        license_plate = license_plate.strip().upper()
        search_attempted = True
        search_query = license_plate
        
        if not license_plate:
            messages.error(request, 'Please enter a license plate number.')
        else:
            try:
                vehicle = Vehicle.objects.get(license_plate=license_plate)
                parking_records = ParkedVehicle.objects.filter(vehicle=vehicle).order_by('-checkin_time')
                
                if not parking_records.exists():
                    messages.info(request, f'No parking history found for {license_plate}.')
                else:
                    total_sessions = parking_records.count()
                    active_sessions = parking_records.filter(checkout_time__isnull=True).count()
                    
                    # Calculate totals
                    for record in parking_records:
                        if record.duration_minutes:
                            total_hours += record.duration_minutes / 60
                        if record.parking_fee:
                            total_fees += float(record.parking_fee)
                    
                    messages.success(request, f'Found {total_sessions} parking session(s) for {license_plate}.')
            
            except Vehicle.DoesNotExist:
                messages.error(request, f'Vehicle "{license_plate}" has no parking history.')
    
    context = {
        'parking_records': parking_records,
        'search_attempted': search_attempted,
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'total_hours': round(total_hours, 1),
        'total_fees': round(total_fees, 2),
        'search_query': search_query
    }
    return render(request, 'vehicle_history.html', context)


@require_http_methods(["GET"])
def api_find_vehicle(request):
    """
    API endpoint to find vehicle location
    Returns JSON response
    """
    license_plate = request.GET.get('plate', '').strip().upper()
    
    if not license_plate:
        return JsonResponse({
            'success': False,
            'message': 'License plate is required'
        }, status=400)
    
    result = ParkingManager.find_vehicle_location(license_plate)
    
    if not result:
        return JsonResponse({
            'success': False,
            'message': f'Vehicle "{license_plate}" not found or not currently parked'
        }, status=404)
    
    return JsonResponse({
        'success': True,
        'data': result
    })


@require_http_methods(["GET"])
def api_parking_lot_status(request, lot_id=None):
    """
    API endpoint to get parking lot status
    Returns JSON response with all spot information
    """
    try:
        if lot_id:
            parking_lot = ParkingLot.objects.get(lot_id=lot_id)
        else:
            parking_lot = ParkingLot.objects.first()
            if not parking_lot:
                return JsonResponse({
                    'success': False,
                    'message': 'No parking lot configured'
                }, status=404)
        
        status = ParkingManager.get_parking_lot_status(parking_lot)
        
        return JsonResponse({
            'success': True,
            'data': status
        })
    
    except ParkingLot.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Parking lot not found'
        }, status=404)


@require_http_methods(["GET"])
def api_parking_statistics(request, lot_id=None, days=7):
    """
    API endpoint to get parking statistics
    """
    try:
        if lot_id:
            parking_lot = ParkingLot.objects.get(lot_id=lot_id)
        else:
            parking_lot = ParkingLot.objects.first()
            if not parking_lot:
                return JsonResponse({
                    'success': False,
                    'message': 'No parking lot configured'
                }, status=404)
        
        stats = ParkingManager.get_parking_statistics(parking_lot, days=int(days))
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
    
    except (ParkingLot.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid parameters'
        }, status=400)


@require_http_methods(["GET"])
def api_recent_activity(request, lot_id=None, hours=24):
    """
    API endpoint to get recent parking activity
    """
    try:
        if lot_id:
            parking_lot = ParkingLot.objects.get(lot_id=lot_id)
        else:
            parking_lot = ParkingLot.objects.first()
            if not parking_lot:
                return JsonResponse({
                    'success': False,
                    'message': 'No parking lot configured'
                }, status=404)
        
        activity = ParkingManager.get_recent_activity(parking_lot, hours=int(hours))
        
        activity_data = [{
            'vehicle_plate': record.vehicle.license_plate,
            'owner_name': record.vehicle.owner_name,
            'spot_number': record.parking_spot.spot_number if record.parking_spot else 'N/A',
            'checkin_time': record.checkin_time.isoformat(),
            'checkout_time': record.checkout_time.isoformat() if record.checkout_time else None,
            'duration': record.get_duration_display(),
            'status': 'active' if record.is_active() else 'completed'
        } for record in activity]
        
        return JsonResponse({
            'success': True,
            'data': activity_data
        })
    
    except (ParkingLot.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid parameters'
        }, status=400)


# YOLOv8 Integration Endpoints


@csrf_exempt
@require_http_methods(["POST"])
def yolov8_webhook(request):
    """
    Webhook endpoint for YOLOv8 vehicle detection
    Receives detected vehicles and automatic license plates
    Process detection data and auto-update parking system
    """
    if not YOLOV8_ENABLED:
        return JsonResponse(
            {'success': False, 'message': 'YOLOv8 not enabled'},
            status=503
        )

    try:
        data = json.loads(request.body)
        detection_data = data.get('detections', [])
        parking_lot_id = data.get('parking_lot_id')
        timestamp = data.get('timestamp', timezone.now().isoformat())

        if not parking_lot_id:
            return JsonResponse(
                {'success': False, 'message': 'parking_lot_id required'},
                status=400
            )

        parking_lot = ParkingLot.objects.get(lot_id=parking_lot_id)
        results = []

        for det in detection_data:
            license_plate = det.get('license_plate')
            spot_number = det.get('spot_number')
            confidence = det.get('confidence', 0.0)
            vehicle_type = det.get('vehicle_type', 'car')

            if not license_plate:
                results.append({'error': 'No license plate detected', 'confidence': confidence})
                continue

            try:
                # Register vehicle
                vehicle = ParkingManager.register_vehicle(
                    license_plate=license_plate,
                    vehicle_type=vehicle_type,
                    owner_name='YOLOv8 Detection',
                    owner_phone='Auto-detected',
                    color=det.get('color', 'Unknown')
                )

                # Find or use specified spot
                if spot_number:
                    parking_spot = ParkingSpot.objects.filter(
                        parking_lot=parking_lot,
                        spot_number=spot_number
                    ).first()
                else:
                    parking_spot = ParkingManager.find_available_spot(parking_lot)

                if parking_spot:
                    # Auto check-in
                    record = ParkingManager.checkin_vehicle(
                        license_plate=license_plate,
                        parking_lot=parking_lot,
                        parking_spot=parking_spot,
                        entry_image_path=det.get('image_path', '')
                    )

                    results.append({
                        'success': True,
                        'license_plate': license_plate,
                        'spot_number': parking_spot.spot_number,
                        'confidence': confidence,
                        'action': 'checked_in'
                    })
                else:
                    results.append({
                        'success': False,
                        'license_plate': license_plate,
                        'error': 'No available parking spots'
                    })

            except Exception as e:
                logger.error(f"Error processing detection: {e}")
                results.append({
                    'success': False,
                    'license_plate': license_plate,
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'parking_lot_id': parking_lot_id,
            'processed_detections': len(detection_data),
            'results': results
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except ParkingLot.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Parking lot not found'}, status=404)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_image_detection(request):
    """
    Process a single image for vehicle detection
    Detects vehicles and extracts license plates
    """
    if not YOLOV8_ENABLED:
        return JsonResponse(
            {'success': False, 'message': 'YOLOv8 not enabled'},
            status=503
        )

    try:
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'message': 'No image provided'}, status=400)

        image_file = request.FILES['image']

        # Read image
        nparr = np.frombuffer(image_file.read(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return JsonResponse({'success': False, 'message': 'Invalid image'}, status=400)

        # Detect vehicles
        detections = VEHICLE_DETECTOR.detect_vehicles(frame)

        results = []
        for det in detections:
            # Extract license plate
            license_plate = LICENSE_PLATE_OCR.extract_license_plate(
                frame,
                det['box']
            )

            results.append({
                'vehicle_type': det['class_name'],
                'confidence': float(det['confidence']),
                'box': [int(x) for x in det['box']],
                'center': [int(x) for x in det['center']],
                'license_plate': license_plate or 'Not detected'
            })

        return JsonResponse({
            'success': True,
            'total_detections': len(detections),
            'detections': results
        })

    except Exception as e:
        logger.error(f"Image detection error: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def detect_license_plate(request):
    """
    Detect and extract license plate from an image
    """
    if not YOLOV8_ENABLED:
        return JsonResponse(
            {'success': False, 'message': 'YOLOv8 not enabled'},
            status=503
        )

    try:
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'message': 'No image provided'}, status=400)

        image_file = request.FILES['image']

        # Read image
        nparr = np.frombuffer(image_file.read(), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return JsonResponse({'success': False, 'message': 'Invalid image'}, status=400)

        # Detect vehicles first
        detections = VEHICLE_DETECTOR.detect_vehicles(frame)

        if not detections:
            return JsonResponse({
                'success': False,
                'message': 'No vehicles detected in image'
            }, status=400)

        # Get largest vehicle (main vehicle in image)
        main_vehicle = max(detections, key=lambda x: x['area'])

        # Extract license plate
        license_plate = LICENSE_PLATE_OCR.extract_license_plate(
            frame,
            main_vehicle['box']
        )

        if not license_plate:
            return JsonResponse({
                'success': False,
                'message': 'Could not extract license plate'
            }, status=400)

        return JsonResponse({
            'success': True,
            'license_plate': license_plate,
            'confidence': float(main_vehicle['confidence']),
            'vehicle_type': main_vehicle['class_name']
        })

    except Exception as e:
        logger.error(f"License plate detection error: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def yolov8_status(request):
    """
    Get current YOLOv8 system status - ADMIN ONLY - BACKEND INFO
    """
    return JsonResponse({
        'yolov8_enabled': YOLOV8_ENABLED,
        'detector_model': 'yolov8n.pt' if YOLOV8_ENABLED else None,
        'ocr_enabled': YOLOV8_ENABLED,
        'status': 'operational' if YOLOV8_ENABLED else 'unavailable',
        'endpoints': [
            '/api/yolov8/webhook/',
            '/api/yolov8/process-image/',
            '/api/yolov8/detect-plate/',
            '/api/yolov8/status/'
        ] if YOLOV8_ENABLED else []
    })

