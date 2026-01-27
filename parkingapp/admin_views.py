"""
Admin Views for Smart Parking Management System
Handles all 15 real-world parking scenarios
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from .smart_parking_manager import SmartParkingManager
from .parking_spot_tracker import ParkingSpotTracker
import pickle
import os
import json
import logging

logger = logging.getLogger(__name__)

# Initialize manager
_parking_manager = None

def get_parking_manager():
    """Get or initialize the parking manager"""
    global _parking_manager
    
    if _parking_manager is None:
        try:
            pos_file = 'parkingapp/CarParkPos'
            if os.path.exists(pos_file):
                with open(pos_file, 'rb') as f:
                    parking_positions = pickle.load(f)
                    tracker = ParkingSpotTracker(parking_positions, 1280, 720)
                    _parking_manager = SmartParkingManager(tracker)
                    logger.info(f"Parking manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize parking manager: {e}")
    
    return _parking_manager


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with all 15 scenarios"""
    manager = get_parking_manager()
    
    if not manager:
        return render(request, 'admin_dashboard.html', {
            'error': 'Parking system not initialized'
        })
    
    context = {
        'page_title': '🚗 Smart Parking Admin Dashboard',
        'dashboard': manager.get_admin_dashboard(),
        'analytics': manager.get_analytics_dashboard(),
        'consistency': manager.verify_data_consistency(),
        'parking_full': manager.get_parking_full_status(),
    }
    
    return render(request, 'admin_dashboard.html', context)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_1_search_vehicle(request):
    """Scenario 1: Search car by vehicle number"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        license_plate = data.get('license_plate', '').strip().upper()
        
        if not license_plate:
            return JsonResponse({'error': 'License plate required'}, status=400)
        
        result = manager.search_vehicle_by_plate(license_plate)
        return JsonResponse({'success': True, 'data': result})
    
    except Exception as e:
        logger.error(f"Error in scenario 1: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def scenario_2_real_time_status(request):
    """Scenario 2: Real-time slot status sync"""
    manager = get_parking_manager()
    
    try:
        status = manager.get_live_parking_status()
        return JsonResponse({'success': True, 'data': status})
    except Exception as e:
        logger.error(f"Error in scenario 2: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_3_detect_mismatch(request):
    """Scenario 3: Detect slot mismatch"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        expected_spot = data.get('expected_spot')
        actual_spot = data.get('actual_spot')
        license_plate = data.get('license_plate', '').upper()
        
        result = manager.detect_slot_mismatch(expected_spot, actual_spot, license_plate)
        return JsonResponse({'success': True, 'data': result})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def scenario_4_parking_full(request):
    """Scenario 4: Handle parking full state"""
    manager = get_parking_manager()
    
    try:
        result = manager.get_parking_full_status()
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_5_parking_duration(request):
    """Scenario 5: Get parking duration"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        license_plate = data.get('license_plate', '').upper()
        
        result = manager.get_parking_duration(license_plate)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def scenario_6_double_parking_check(request):
    """Scenario 6: Check for double parking"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        license_plate = data.get('license_plate', '').upper()
        
        result = manager.check_already_parked(license_plate)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_7_unauthorized_detection(request):
    """Scenario 7: Detect unauthorized vehicles"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        license_plate = data.get('license_plate', '').upper()
        
        result = manager.detect_unauthorized_vehicle(license_plate)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_8_camera_failure(request):
    """Scenario 8: Handle camera failures"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        action = data.get('action')  # 'failure' or 'recovery'
        camera_id = data.get('camera_id')
        
        if action == 'failure':
            result = manager.handle_camera_failure(camera_id)
        else:
            result = manager.camera_recovery(camera_id)
        
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_9_entry_exit(request):
    """Scenario 9: Entry/Exit management"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        action = data.get('action')  # 'entry' or 'exit'
        license_plate = data.get('license_plate', '').upper()
        gate = data.get('gate', 'Gate A')
        
        if action == 'entry':
            result = manager.register_vehicle_entry(license_plate, gate)
        else:
            result = manager.register_vehicle_exit(license_plate, gate)
        
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def scenario_10_nearest_spot(request):
    """Scenario 10: Find nearest available slot"""
    manager = get_parking_manager()
    
    try:
        result = manager.find_nearest_available_spot()
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def scenario_11_analytics(request):
    """Scenario 11: Get analytics dashboard"""
    manager = get_parking_manager()
    
    try:
        result = manager.get_analytics_dashboard()
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_12_notifications(request):
    """Scenario 12: Send notifications"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        user_plate = data.get('user_plate', '').upper()
        notification_type = data.get('type')
        
        result = manager.send_notification(user_plate, notification_type)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def scenario_13_admin_panel(request):
    """Scenario 13: Admin panel with search and filter"""
    manager = get_parking_manager()
    
    try:
        dashboard = manager.get_admin_dashboard()
        return JsonResponse({'success': True, 'data': dashboard})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def scenario_14_data_verification(request):
    """Scenario 14: Data accuracy verification"""
    manager = get_parking_manager()
    
    try:
        result = manager.verify_data_consistency()
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def scenario_15_manual_override(request):
    """Scenario 15: Manual override for slot status"""
    manager = get_parking_manager()
    
    try:
        data = json.loads(request.body) if request.body else {}
        spot_id = data.get('spot_id')
        action = data.get('action')  # 'MARK_OCCUPIED' or 'MARK_AVAILABLE'
        admin_id = request.user.id
        reason = data.get('reason', 'No reason provided')
        
        result = manager.manual_override_slot_status(spot_id, action, admin_id, reason)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
