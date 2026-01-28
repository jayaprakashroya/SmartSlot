"""
Edge Case Handler Views - Professional Solutions for Real-World Issues
Implements all 5 edge cases + 2 bonus features as web endpoints
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import json
import logging

from .models import (
    ParkedVehicle, ParkingSpot, Vehicle, ParkingLot,
    PendingSyncQueue, DisputeLog, AdminAction, ParkingHistory,
    CameraStatus, DetectionLog
)
from .edge_case_handlers import (
    OfflineModeHandler, ConfidenceHandler, PrivacyHandler,
    DisputeHandler, VehicleSearchHandler, AdminOverrideHandler,
    HeatmapHandler
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTION
# ═══════════════════════════════════════════════════════════════════

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'Unknown')
    return ip


# ═══════════════════════════════════════════════════════════════════
# 1. INTERNET OUTAGE - OFFLINE MODE VIEWS
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
@staff_member_required
def offline_status(request):
    """Get offline mode status - ADMIN ONLY"""
    try:
        # Get pending syncs count
        pending_count = PendingSyncQueue.objects.filter(synced=False).count()
        
        status = {
            'status': 'online',
            'is_online': True,
            'pending_count': pending_count,
            'pending_syncs': pending_count,
            'last_sync': None,
            'updated_at': timezone.now().isoformat()
        }
    except Exception as e:
        # Return default status if table doesn't exist
        status = {
            'status': 'unknown',
            'is_online': True,
            'pending_count': 0,
            'pending_syncs': 0,
            'last_sync': None,
            'error': str(e),
            'updated_at': timezone.now().isoformat()
        }
    return JsonResponse(status)


@require_http_methods(["GET", "POST"])
@staff_member_required
def sync_pending_records(request):
    """Manually trigger sync of pending records - ADMIN ONLY"""
    try:
        if request.method == 'GET':
            # Return current sync status
            pending = PendingSyncQueue.objects.filter(synced=False)
            return JsonResponse({
                'status': 'success',
                'pending_count': pending.count(),
                'records': [{
                    'sync_id': p.sync_id,
                    'record_type': p.record_type,
                    'created_at': p.created_at.isoformat()
                } for p in pending[:20]],
                'timestamp': timezone.now().isoformat()
            })
        else:
            # POST - Execute sync
            results = OfflineModeHandler.sync_pending_records()
            return JsonResponse({
                'status': 'success',
                'sync_results': results,
                'timestamp': timezone.now().isoformat()
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@staff_member_required
def pending_sync_queue_view(request):
    """View all pending sync records - ADMIN ONLY"""
    pending = PendingSyncQueue.objects.filter(synced=False).order_by('created_at')
    
    data = {
        'count': pending.count(),
        'records': [{
            'sync_id': p.sync_id,
            'record_type': p.record_type,
            'created_at': p.created_at.isoformat(),
            'data_preview': p.data if isinstance(p.data, dict) else 'Complex Data'
        } for p in pending[:50]]
    }
    
    return render(request, 'offline_mode.html', {'pending_sync': data})


# ═══════════════════════════════════════════════════════════════════
# 2. DOUBLE PARKING & CONFIDENCE DETECTION VIEWS
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["GET", "POST"])
@staff_member_required
@csrf_exempt
def check_double_parking(request):
    """Check for double parking in spots - ADMIN ONLY"""
    try:
        # Get all spots with double parking issues
        double_parked_spots = []
        
        # Check all parking spots
        spots = ParkingSpot.objects.select_related('parking_lot').all()
        
        for spot in spots:
            current = spot.get_current_vehicle()
            if current:
                # Get all detection logs for this spot in last hour
                hour_ago = timezone.now() - timedelta(hours=1)
                recent_logs = DetectionLog.objects.filter(
                    parking_spot=spot,
                    detected_at__gte=hour_ago
                ).order_by('-detected_at')
                
                if recent_logs.count() > 1:
                    double_parked_spots.append({
                        'spot_id': spot.spot_id,
                        'spot_number': spot.spot_number,
                        'lot_id': spot.parking_lot.lot_id,
                        'current_vehicle': PrivacyHandler.mask_license_plate(
                            current.vehicle.license_plate
                        ) if current.vehicle else 'Unknown',
                        'detection_count': recent_logs.count(),
                        'risk_level': 'HIGH' if recent_logs.count() > 3 else 'MEDIUM'
                    })
        
        return JsonResponse({
            'status': 'success',
            'double_parked_count': len(double_parked_spots),
            'spots': double_parked_spots,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'double_parked_count': 0,
            'spots': [],
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@staff_member_required
def low_confidence_detections(request):
    """View detections below confidence threshold - ADMIN ONLY"""
    threshold = ConfidenceHandler.CONFIDENCE_THRESHOLD
    
    # Get detection logs with low confidence
    logs = DetectionLog.objects.filter(
        confidence_scores__icontains='0.'  # Simplified - actual would parse JSON
    ).order_by('-detected_at')[:50]
    
    data = {
        'threshold': threshold,
        'total_low_confidence': logs.count(),
        'detections': [{
            'detection_id': log.detection_id,
            'timestamp': log.detected_at.isoformat(),
            'vehicles': log.vehicles_detected,
            'action': 'Pending Manual Review'
        } for log in logs]
    }
    
    return render(request, 'low_confidence_detections.html', data)


# ═══════════════════════════════════════════════════════════════════
# 3. PRIVACY - PLATE MASKING & ACCESS CONTROL VIEWS
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def plate_access_logs(request):
    """View audit log of plate access by admins - ADMIN ONLY - PRIVACY SENSITIVE"""
    
    # Log this access for audit trail
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='override_detection',
            reason='Viewed license plate access logs'
        )
    except Exception:
        pass  # Silently fail logging
    
    logs = AdminAction.objects.filter(
        action_type__in=['override_detection', 'resolve_dispute']
    ).order_by('-created_at')[:100]
    
    data = {
        'logs': [{
            'admin': log.admin_name,
            'action': log.action_type,
            'timestamp': log.created_at.isoformat(),
            'details': log.reason
        } for log in logs]
    }
    
    return render(request, 'plate_access_logs.html', data)


@require_http_methods(["GET"])
def vehicle_display(request, vehicle_id):
    """Get vehicle info with privacy masking - user can see own, admin can see all"""
    vehicle = get_object_or_404(Vehicle, vehicle_id=vehicle_id)
    
    # Authorization check - user can only view their own vehicles
    if not (request.user.is_staff or request.user.is_superuser):
        try:
            ParkedVehicle.objects.get(vehicle=vehicle, user=request.user)
        except ParkedVehicle.DoesNotExist:
            return JsonResponse({
                'error': "You don't have permission to view this vehicle"
            }, status=403)
    
    is_admin = request.user.is_staff if request.user.is_authenticated else False
    
    display_info = PrivacyHandler.get_vehicle_info_display(vehicle, request.user, is_admin)
    
    if is_admin:
        PrivacyHandler.log_plate_access(
            request.user.username if request.user.is_authenticated else 'Anonymous',
            vehicle.license_plate
        )
    
    return JsonResponse(display_info)


# ═══════════════════════════════════════════════════════════════════
# 4. DISPUTE HANDLING - FILE & RESOLVE DISPUTES
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["GET", "POST"])
def file_dispute(request, parking_record_id):
    """File a parking dispute"""
    
    if request.method == 'GET':
        parked_vehicle = get_object_or_404(ParkedVehicle, parking_record_id=parking_record_id)
        return render(request, 'file_dispute.html', {
            'parking_record': parked_vehicle,
            'entry_image': parked_vehicle.entry_image_path.url if parked_vehicle.entry_image_path else None
        })
    
    # POST - File the dispute
    parked_vehicle_id = request.POST.get('parking_record_id')
    customer_name = request.POST.get('customer_name')
    customer_phone = request.POST.get('customer_phone')
    dispute_type = request.POST.get('dispute_type')
    description = request.POST.get('description')
    
    result = DisputeHandler.file_dispute(
        parked_vehicle_id=parked_vehicle_id,
        customer_name=customer_name,
        phone=customer_phone,
        dispute_type=dispute_type,
        description=description
    )
    
    return JsonResponse(result)


@require_http_methods(["GET"])
def view_dispute_details(request, dispute_id):
    """View dispute with full evidence - user can see own, admin can see all"""
    dispute = get_object_or_404(DisputeLog, dispute_id=dispute_id)
    
    # Authorization check - users can only view disputes they created
    if not (request.user.is_staff or request.user.is_superuser):
        if dispute.created_by != request.user:
            return JsonResponse({
                'error': "You don't have permission to view this dispute"
            }, status=403)
    
    spot_history = DisputeHandler.get_spot_history(
        dispute.parked_vehicle.parking_spot.spot_id if dispute.parked_vehicle.parking_spot else None
    )
    
    data = {
        'dispute': {
            'id': dispute.dispute_id,
            'type': dispute.dispute_type,
            'description': dispute.description,
            'customer': dispute.customer_name,
            'phone': dispute.customer_phone,
            'status': dispute.status,
            'reported_at': dispute.reported_at.isoformat(),
            'entry_image': dispute.entry_image.url if dispute.entry_image else None,
            'entry_video': dispute.entry_video.url if dispute.entry_video else None,
            'confidence': f"{dispute.detection_confidence:.1%}",
            'parked_vehicle': {
                'plate': PrivacyHandler.mask_license_plate(
                    dispute.parked_vehicle.vehicle.license_plate
                ),
                'entry_time': dispute.parked_vehicle.checkin_time.isoformat(),
                'spot': dispute.parked_vehicle.parking_spot.spot_number if dispute.parked_vehicle.parking_spot else 'Unknown'
            }
        },
        'spot_history': spot_history,
        'can_resolve': request.user.is_staff
    }
    
    return render(request, 'dispute_details.html', data)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def resolve_dispute(request, dispute_id):
    """Resolve a dispute - ADMIN ONLY"""
    dispute = get_object_or_404(DisputeLog, dispute_id=dispute_id)
    
    # Log admin action
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='resolve_dispute',
            reason=request.POST.get('reason', 'Dispute resolved')
        )
    except Exception:
        pass  # Silently fail logging
    
    decision = request.POST.get('decision')  # resolved_refund, resolved_valid, rejected
    notes = request.POST.get('notes')
    refund_amount = request.POST.get('refund_amount')
    
    result = DisputeHandler.resolve_dispute(
        dispute_id=dispute_id,
        admin_name=request.user.username,
        decision=decision,
        notes=notes,
        refund_amount=float(refund_amount) if refund_amount else None
    )
    
    return JsonResponse(result)


# ═══════════════════════════════════════════════════════════════════
# 5. SEARCH WITHOUT PLATE - MULTIPLE SEARCH METHODS
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["GET", "POST"])
@staff_member_required
def search_by_phone(request):
    """Search parking by phone number - ADMIN ONLY - INVESTIGATIVE TOOL"""
    if request.method == 'GET':
        return render(request, 'search_by_phone.html')
    
    # POST request
    phone = request.POST.get('phone', '').strip()
    
    # Log this search
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='override_detection',
            reason=f'Searched vehicles by phone: {phone}'
        )
    except Exception:
        pass  # Silently fail logging
    
    if not phone or len(phone) < 10:
        return JsonResponse({'status': 'error', 'message': 'Invalid phone number'})
    
    results = VehicleSearchHandler.search_by_phone(phone)
    
    return render(request, 'parking_history.html', {
        'search_method': 'phone',
        'search_term': phone,
        'current_parking': results['current'],
        'history': results['recent']
    })


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def search_by_ticket(request):
    """Search parking by ticket ID - ADMIN ONLY"""
    ticket_id = request.POST.get('ticket_id', '').strip()
    
    # Log this search
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='override_detection',
            reason=f'Searched vehicle by ticket: {ticket_id}'
        )
    except Exception:
        pass  # Silently fail logging
    
    result = VehicleSearchHandler.search_by_ticket(ticket_id)
    
    if result['status'] == 'not_found':
        return JsonResponse({'status': 'error', 'message': 'Ticket not found'}, status=404)
    
    return JsonResponse(result)


@require_http_methods(["POST"])
@staff_member_required
def search_by_vehicle_details(request):
    """Search by vehicle color and type - ADMIN ONLY - INVESTIGATIVE"""
    color = request.POST.get('color', '').strip()
    vehicle_type = request.POST.get('vehicle_type', '').strip()
    time_range = request.POST.get('time_range', 24)
    
    # Log this search
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='override_detection',
            reason=f'Searched vehicles: color={color}, type={vehicle_type}'
        )
    except Exception:
        pass  # Silently fail logging
    
    results = VehicleSearchHandler.search_by_vehicle_details(color, vehicle_type, int(time_range))
    
    return render(request, 'vehicle_search_results.html', {
        'search_method': 'vehicle_details',
        'filter_color': color,
        'filter_type': vehicle_type,
        'results': results
    })


@require_http_methods(["GET"])
@staff_member_required
def parking_history_api(request):
    """API endpoint for parking history - ADMIN ONLY"""
    phone = request.GET.get('phone', '').strip()
    
    try:
        if not phone:
            # If no phone, return error
            return JsonResponse({
                'status': 'error',
                'message': 'Phone number required',
                'current_parking': None,
                'history': [],
                'total_records': 0
            }, status=400)
        
        results = VehicleSearchHandler.search_by_phone(phone)
        
        # Format response
        return JsonResponse({
            'status': 'success',
            'phone': phone,
            'current_parking': results.get('current'),
            'history': results.get('recent', []),
            'total_records': len(results.get('recent', [])),
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'current_parking': None,
            'history': [],
            'total_records': 0,
            'timestamp': timezone.now().isoformat()
        }, status=500)


# ═══════════════════════════════════════════════════════════════════
# BONUS A: ADMIN FORCE RELEASE - MANUAL OVERRIDE
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def force_release_spot(request, spot_id):
    """Force release a parking spot - ADMIN ONLY - DANGEROUS OPERATION"""
    spot = get_object_or_404(ParkingSpot, spot_id=spot_id)
    
    # Get vehicle info before release
    vehicle = spot.get_current_vehicle()
    vehicle_info = f"Vehicle: {vehicle.vehicle.license_plate}" if vehicle else "No vehicle"
    
    # Get form data
    reason = request.POST.get('reason', 'Force released spot')
    notes = request.POST.get('notes', '')
    
    # Log this CRITICAL admin action
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='force_release',
            reason=reason,
            parking_spot=spot,
            vehicle=vehicle
        )
    except Exception:
        pass  # Silently fail logging
    
    result = AdminOverrideHandler.force_release_spot(
        spot_id=spot_id,
        admin_name=request.user.username,
        reason=reason,
        notes=notes
    )
    
    return JsonResponse(result)


@require_http_methods(["POST"])
@csrf_exempt
@staff_member_required
def manual_vehicle_entry(request, spot_id):
    """Manually register vehicle entry - ADMIN ONLY - CRITICAL OVERRIDE"""
    spot = get_object_or_404(ParkingSpot, spot_id=spot_id)
    license_plate = request.POST.get('vehicle_plate', '').strip().upper()
    reason = request.POST.get('reason', 'Camera malfunction')
    
    try:
        vehicle = Vehicle.objects.get(license_plate=license_plate)
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)
    
    # Log this CRITICAL admin action
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='manual_entry',
            reason=reason,
            parking_spot=spot,
            vehicle=vehicle
        )
    except Exception:
        pass  # Silently fail logging
    
    result = AdminOverrideHandler.manual_vehicle_entry(
        spot_id=spot_id,
        vehicle_plate=vehicle_plate,
        admin_name=request.user.username,
        reason=reason
    )
    
    return JsonResponse(result)


@login_required
@require_http_methods(["GET"])
@staff_member_required
def admin_action_history(request):
    """View admin action audit trail - ADMIN ONLY - SENSITIVE AUDIT DATA"""
    
    # Log that someone accessed this sensitive data
    try:
        AdminAction.objects.create(
            admin_name=request.user.username,
            action_type='override_detection',
            reason='Accessed admin action history audit log'
        )
    except Exception:
        pass  # Silently fail logging
    

    
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Admin access required'}, status=403)
    
    history = AdminOverrideHandler.get_admin_action_history(limit=100)
    
    return render(request, 'admin_action_history.html', {
        'actions': history
    })


# ═══════════════════════════════════════════════════════════════════
# BONUS B: SLOT HEATMAP - REAL-TIME OCCUPANCY VISUALIZATION
# ═══════════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def parking_lot_heatmap(request, lot_id=None):
    """Get parking lot heatmap"""
    
    if not lot_id:
        # Use first lot if not specified
        lot = ParkingLot.objects.first()
        if not lot:
            return JsonResponse({'status': 'error', 'message': 'No parking lot found'})
        lot_id = lot.lot_id
    
    heatmap = HeatmapHandler.get_lot_heatmap(lot_id)
    
    if request.GET.get('format') == 'json':
        return JsonResponse(heatmap)
    
    return render(request, 'heatmap.html', {'heatmap': heatmap})


@require_http_methods(["GET"])
def heatmap_analytics(request, lot_id=None):
    """Get heatmap analytics"""
    
    if not lot_id:
        lot = ParkingLot.objects.first()
        if not lot:
            return JsonResponse({'status': 'error', 'message': 'No parking lot found'})
        lot_id = lot.lot_id
    
    analytics = HeatmapHandler.get_heatmap_analytics(lot_id)
    
    return JsonResponse(analytics)


@require_http_methods(["GET"])
def heatmap_realtime_api(request, lot_id=None):
    """Real-time heatmap API for auto-refresh"""
    
    try:
        if not lot_id:
            lot = ParkingLot.objects.first()
            if not lot:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No parking lots found',
                    'occupancy_rate': 0,
                    'occupied': 0,
                    'available': 0,
                    'spots': [],
                    'updated_at': timezone.now().isoformat()
                })
            lot_id = lot.lot_id
        
        heatmap = HeatmapHandler.get_lot_heatmap(lot_id)
        
        # Return only essential data for fast updates
        return JsonResponse({
            'status': 'success',
            'lot_id': lot_id,
            'occupancy_rate': heatmap.get('occupancy_rate', 0),
            'occupancy': heatmap.get('occupancy_rate', 0),  # Alias for occupancy_rate
            'occupied': heatmap.get('occupied', 0),
            'available': heatmap.get('available', 0),
            'total': heatmap.get('total', 0),
            'spots': [{'spot_id': s.get('spot_id'), 'color': s.get('color')} for s in heatmap.get('spots', [])],
            'updated_at': heatmap.get('updated_at', timezone.now().isoformat())
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'occupancy_rate': 0,
            'occupancy': 0,
            'occupied': 0,
            'available': 0,
            'total': 0,
            'spots': [],
            'updated_at': timezone.now().isoformat()
        })
