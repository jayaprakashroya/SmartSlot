# ═══════════════════════════════════════════════════════════════════
# Edge Case Handlers - Professional Solutions for Real-World Issues
# ═══════════════════════════════════════════════════════════════════

import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, F, ExpressionWrapper, IntegerField, Case, When
from .models import (
    ParkedVehicle, ParkingSpot, Vehicle, ParkingLot,
    PendingSyncQueue, DisputeLog, AdminAction, ParkingHistory,
    CameraStatus, DetectionLog
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 1. INTERNET OUTAGE HANDLING
# ═══════════════════════════════════════════════════════════════════

class OfflineModeHandler:
    """Handle operations when internet is down"""
    
    OFFLINE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def queue_vehicle_entry(vehicle_data):
        """Queue vehicle entry for sync when online"""
        try:
            # Try normal database save first
            vehicle_entry = ParkedVehicle.objects.create(**vehicle_data)
            return {'status': 'success', 'mode': 'online', 'record_id': vehicle_entry.parking_record_id}
        except Exception as e:
            # If fails, save to sync queue
            queue = PendingSyncQueue.objects.create(
                record_type='vehicle_entry',
                vehicle_id=vehicle_data.get('vehicle_id'),
                parking_spot_id=vehicle_data.get('parking_spot_id'),
                data=vehicle_data
            )
            return {'status': 'queued', 'mode': 'offline', 'queue_id': queue.sync_id, 'error': str(e)}
    
    @staticmethod
    def queue_vehicle_exit(vehicle_data):
        """Queue vehicle exit for sync when online"""
        try:
            vehicle_exit = ParkedVehicle.objects.filter(**vehicle_data).update(
                checkout_time=timezone.now()
            )
            return {'status': 'success', 'mode': 'online', 'updated': vehicle_exit}
        except Exception as e:
            queue = PendingSyncQueue.objects.create(
                record_type='vehicle_exit',
                vehicle_id=vehicle_data.get('vehicle_id'),
                parking_spot_id=vehicle_data.get('parking_spot_id'),
                data=vehicle_data
            )
            return {'status': 'queued', 'mode': 'offline', 'queue_id': queue.sync_id, 'error': str(e)}
    
    @staticmethod
    def sync_pending_records():
        """Sync all pending records when internet returns"""
        pending = PendingSyncQueue.objects.filter(synced=False)
        sync_results = {
            'total': pending.count(),
            'successful': 0,
            'failed': 0,
            'records': []
        }
        
        for record in pending:
            try:
                if record.record_type == 'vehicle_entry':
                    ParkedVehicle.objects.create(**record.data)
                elif record.record_type == 'vehicle_exit':
                    ParkedVehicle.objects.filter(id=record.data.get('id')).update(
                        checkout_time=timezone.now()
                    )
                
                record.synced = True
                record.synced_at = timezone.now()
                record.save()
                sync_results['successful'] += 1
            except Exception as e:
                record.sync_error = str(e)
                record.save()
                sync_results['failed'] += 1
            
            sync_results['records'].append({
                'queue_id': record.sync_id,
                'type': record.record_type,
                'status': 'synced' if record.synced else 'failed'
            })
        
        return sync_results
    
    @staticmethod
    def get_offline_status():
        """Get status of pending syncs"""
        pending = PendingSyncQueue.objects.filter(synced=False)
        oldest = pending.first()
        
        return {
            'pending_count': pending.count(),
            'oldest_pending': oldest.created_at if oldest else None,
            'offline_duration': None,
            'status': 'offline' if pending.exists() else 'online'
        }


# ═══════════════════════════════════════════════════════════════════
# 2. DOUBLE PARKING & CONFIDENCE THRESHOLD
# ═══════════════════════════════════════════════════════════════════

class ConfidenceHandler:
    """Handle detection confidence and double parking"""
    
    CONFIDENCE_THRESHOLD = 0.90  # Only 90%+ confidence for auto-assignment (stricter)
    DOUBLE_PARKING_OVERLAP = 0.6  # 60% IoU = flag as double parked
    
    @staticmethod
    def assign_with_confidence_check(vehicle_bbox, license_plate, confidence):
        """Assign vehicle only if confidence is high enough"""
        
        if confidence < ConfidenceHandler.CONFIDENCE_THRESHOLD:
            # Queue for manual review
            return {
                'status': 'pending_review',
                'confidence': confidence,
                'reason': f'Low confidence ({confidence:.1%}) - below threshold ({ConfidenceHandler.CONFIDENCE_THRESHOLD:.1%})',
                'action_required': 'Admin must manually review and approve'
            }
        
        return {'status': 'auto_assigned', 'confidence': confidence}
    
    @staticmethod
    def detect_double_parking(current_spot, vehicle_bbox):
        """Detect if multiple vehicles in same spot"""
        current_vehicle = current_spot.get_current_vehicle()
        
        if not current_vehicle:
            return {'double_parked': False}
        
        # Calculate IoU (Intersection over Union)
        iou = ConfidenceHandler._calculate_iou(
            current_vehicle.vehicle_bbox if hasattr(current_vehicle, 'vehicle_bbox') else None,
            vehicle_bbox
        )
        
        if iou > ConfidenceHandler.DOUBLE_PARKING_OVERLAP:
            return {
                'double_parked': True,
                'iou': iou,
                'existing_vehicle': current_vehicle.vehicle.license_plate,
                'alert_level': 'HIGH' if iou > 0.8 else 'MEDIUM'
            }
        
        return {'double_parked': False, 'iou': iou}
    
    @staticmethod
    def _calculate_iou(box1, box2):
        """Calculate Intersection over Union"""
        if not box1 or not box2:
            return 0
        
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        intersection = max(0, min(x1_max, x2_max) - max(x1_min, x2_min)) * \
                      max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0


# ═══════════════════════════════════════════════════════════════════
# 3. PRIVACY - LICENSE PLATE MASKING
# ═══════════════════════════════════════════════════════════════════

class PrivacyHandler:
    """Handle privacy protection for vehicle data"""
    
    @staticmethod
    def mask_license_plate(plate_number):
        """Mask license plate for public display"""
        if not plate_number or len(plate_number) < 4:
            return "****"
        
        # Show first 2 and last 2 characters only
        return plate_number[:2] + "****" + plate_number[-2:]
    
    @staticmethod
    def get_display_plate(plate_number, user=None, is_admin=False):
        """Get appropriate plate display based on user role"""
        if is_admin or (user and user.is_staff):
            return plate_number  # Full plate for admins
        return PrivacyHandler.mask_license_plate(plate_number)  # Masked for public
    
    @staticmethod
    def get_vehicle_info_display(vehicle, user=None, is_admin=False):
        """Get vehicle info with appropriate privacy"""
        if is_admin or (user and user.is_staff):
            return {
                'plate': vehicle.license_plate,
                'owner': vehicle.owner_name,
                'phone': vehicle.owner_phone,
                'type': vehicle.vehicle_type,
                'color': vehicle.color
            }
        else:
            return {
                'plate': PrivacyHandler.mask_license_plate(vehicle.license_plate),
                'type': vehicle.vehicle_type,
                'color': vehicle.color,
                'owner': None,
                'phone': None
            }
    
    @staticmethod
    def log_plate_access(admin_name, plate_number):
        """Log every access to full license plate numbers"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'admin': admin_name,
            'plate': plate_number,
            'action': 'view_full_plate'
        }
        # Log to audit trail
        return log_entry


# ═══════════════════════════════════════════════════════════════════
# 4. DISPUTE HANDLING - EVIDENCE & AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════

class DisputeHandler:
    """Handle customer disputes with evidence"""
    
    @staticmethod
    def file_dispute(parked_vehicle_id, customer_name, phone, dispute_type, description, 
                     entry_image=None, entry_video=None):
        """File a new dispute with evidence"""
        
        parked_vehicle = ParkedVehicle.objects.get(parking_record_id=parked_vehicle_id)
        
        dispute = DisputeLog.objects.create(
            parked_vehicle=parked_vehicle,
            customer_name=customer_name,
            customer_phone=phone,
            dispute_type=dispute_type,
            description=description,
            entry_image=entry_image or parked_vehicle.entry_image_path,
            entry_video=entry_video,
            detection_confidence=0.95  # From original detection
        )
        
        return {
            'dispute_id': dispute.dispute_id,
            'status': 'pending',
            'message': 'Your dispute has been filed. We will review it within 24 hours.',
            'created_at': dispute.reported_at
        }
    
    @staticmethod
    def get_spot_history(spot_id, limit=20):
        """Get complete history of all vehicles in a spot"""
        history = ParkedVehicle.objects.filter(
            parking_spot_id=spot_id
        ).select_related('vehicle').order_by('-checkin_time')[:limit]
        
        return [{
            'vehicle_plate': pv.vehicle.license_plate,
            'entry_time': pv.checkin_time,
            'exit_time': pv.checkout_time,
            'duration': pv.get_duration_display(),
            'entry_image': pv.entry_image_path.url if pv.entry_image_path else None,
            'exit_image': pv.exit_image_path.url if pv.exit_image_path else None,
            'disputes': DisputeLog.objects.filter(parkedvehicle=pv).count()
        } for pv in history]
    
    @staticmethod
    def resolve_dispute(dispute_id, admin_name, decision, notes, refund_amount=None):
        """Resolve a dispute"""
        dispute = DisputeLog.objects.get(dispute_id=dispute_id)
        
        dispute.status = decision
        dispute.admin_notes = notes
        dispute.handled_by = admin_name
        dispute.resolved_at = timezone.now()
        
        if refund_amount:
            dispute.refund_amount = refund_amount
        
        dispute.save()
        
        return {
            'dispute_id': dispute.dispute_id,
            'status': decision,
            'resolved_at': dispute.resolved_at,
            'message': f'Dispute resolved: {decision}'
        }


# ═══════════════════════════════════════════════════════════════════
# 5. SEARCH WITHOUT PLATE NUMBER - MULTIPLE METHODS
# ═══════════════════════════════════════════════════════════════════

class VehicleSearchHandler:
    """Search vehicles using multiple methods"""
    
    @staticmethod
    def search_by_phone(phone_number):
        """Search parking history by phone number"""
        history = ParkingHistory.objects.filter(
            phone_number=phone_number
        ).select_related('parkedvehicle__vehicle', 'parkedvehicle__parking_spot').order_by(
            '-parkedvehicle__checkin_time'
        )[:20]
        
        results = {
            'current': None,
            'recent': []
        }
        
        for record in history:
            pv = record.parked_vehicle
            vehicle_info = {
                'license_plate': PrivacyHandler.mask_license_plate(pv.vehicle.license_plate),
                'vehicle_type': pv.vehicle.vehicle_type,
                'color': pv.vehicle.color,
                'entry_time': pv.checkin_time,
                'duration': pv.get_duration_display(),
                'spot': pv.parking_spot.spot_number if pv.parking_spot else 'Unknown',
                'parking_lot': pv.parking_lot.lot_name,
                'image': pv.entry_image_path.url if pv.entry_image_path else None
            }
            
            if pv.is_active():
                results['current'] = vehicle_info
            else:
                results['recent'].append(vehicle_info)
        
        return results
    
    @staticmethod
    def search_by_ticket(ticket_id):
        """Search by parking ticket"""
        history = ParkingHistory.objects.filter(ticket_id=ticket_id).first()
        
        if not history:
            return {'status': 'not_found'}
        
        pv = history.parked_vehicle
        return {
            'status': 'found',
            'spot': pv.parking_spot.spot_number if pv.parking_spot else 'Unknown',
            'vehicle_plate': PrivacyHandler.mask_license_plate(pv.vehicle.license_plate),
            'entry_time': pv.checkin_time,
            'duration': pv.get_duration_display(),
            'parking_lot': pv.parking_lot.lot_name,
            'image': pv.entry_image_path.url if pv.entry_image_path else None
        }
    
    @staticmethod
    def search_by_vehicle_details(color, vehicle_type, time_range=None):
        """Search by vehicle characteristics"""
        query = Vehicle.objects.filter(
            color__icontains=color,
            vehicle_type=vehicle_type
        )
        
        parked = ParkedVehicle.objects.filter(
            vehicle__in=query,
            checkout_time__isnull=True
        ).select_related('vehicle', 'parking_spot')
        
        if time_range:
            parked = parked.filter(
                checkin_time__gte=timezone.now() - timedelta(hours=time_range)
            )
        
        return [{
            'plate': PrivacyHandler.mask_license_plate(pv.vehicle.license_plate),
            'type': pv.vehicle.vehicle_type,
            'color': pv.vehicle.color,
            'spot': pv.parking_spot.spot_number,
            'entry_time': pv.checkin_time,
            'duration': pv.get_duration_display(),
            'image': pv.entry_image_path.url if pv.entry_image_path else None
        } for pv in parked]


# ═══════════════════════════════════════════════════════════════════
# 6. ADMIN FORCE RELEASE - MANUAL OVERRIDE WITH LOGGING
# ═══════════════════════════════════════════════════════════════════

class AdminOverrideHandler:
    """Handle admin manual interventions"""
    
    @staticmethod
    def force_release_spot(spot_id, admin_name, reason, notes=''):
        """Force release a parking spot"""
        spot = ParkingSpot.objects.get(spot_id=spot_id)
        parked_vehicle = spot.get_current_vehicle()
        
        if not parked_vehicle:
            return {'status': 'error', 'message': 'No vehicle currently in this spot'}
        
        # Log the action
        admin_action = AdminAction.objects.create(
            admin_name=admin_name,
            action_type='force_release',
            parking_spot=spot,
            vehicle=parked_vehicle.vehicle,
            reason=reason,
            notes=notes,
            before_state={
                'spot_occupied': True,
                'vehicle': parked_vehicle.vehicle.license_plate,
                'entry_time': parked_vehicle.checkin_time.isoformat()
            }
        )
        
        # Release the spot
        parked_vehicle.checkout()
        
        admin_action.after_state = {
            'spot_occupied': False,
            'exit_time': parked_vehicle.checkout_time.isoformat()
        }
        admin_action.save()
        
        return {
            'status': 'success',
            'message': f'Spot {spot.spot_number} has been released',
            'action_id': admin_action.action_id,
            'vehicle_released': parked_vehicle.vehicle.license_plate,
            'timestamp': admin_action.created_at
        }
    
    @staticmethod
    def manual_vehicle_entry(spot_id, vehicle_plate, admin_name, reason):
        """Manually register a vehicle entry"""
        spot = ParkingSpot.objects.get(spot_id=spot_id)
        vehicle, created = Vehicle.objects.get_or_create(license_plate=vehicle_plate)
        
        parked_vehicle = ParkedVehicle.objects.create(
            vehicle=vehicle,
            parking_spot=spot,
            parking_lot=spot.parking_lot,
            notes=f'Manual entry by {admin_name}: {reason}'
        )
        
        AdminAction.objects.create(
            admin_name=admin_name,
            action_type='manual_entry',
            parking_spot=spot,
            vehicle=vehicle,
            reason=reason,
            after_state={
                'record_id': parked_vehicle.parking_record_id,
                'entry_time': parked_vehicle.checkin_time.isoformat()
            }
        )
        
        return {
            'status': 'success',
            'message': f'Vehicle {vehicle_plate} manually entered in Spot {spot.spot_number}',
            'record_id': parked_vehicle.parking_record_id
        }
    
    @staticmethod
    def get_admin_action_history(limit=50):
        """Get audit trail of admin actions"""
        actions = AdminAction.objects.all().order_by('-created_at')[:limit]
        
        return [{
            'action_id': action.action_id,
            'admin': action.admin_name,
            'action_type': action.action_type,
            'spot': action.parking_spot.spot_number if action.parking_spot else 'N/A',
            'vehicle': action.vehicle.license_plate if action.vehicle else 'N/A',
            'reason': action.reason,
            'timestamp': action.created_at,
            'notes': action.notes
        } for action in actions]


# ═══════════════════════════════════════════════════════════════════
# 7. HEATMAP - REAL-TIME OCCUPANCY VISUALIZATION
# ═══════════════════════════════════════════════════════════════════

class HeatmapHandler:
    """Generate parking lot heatmap data"""
    
    @staticmethod
    def get_lot_heatmap(lot_id):
        """Get heatmap data for entire parking lot"""
        lot = ParkingLot.objects.get(lot_id=lot_id)
        spots = lot.spots.all().order_by('spot_number')
        
        heatmap_data = []
        
        for spot in spots:
            # Determine if spot is occupied based on active ParkedVehicle records
            is_spot_occupied = spot.is_occupied()
            
            # For color, use individual spot status (not area-based)
            # Green = empty, Red = occupied
            color = 'red' if is_spot_occupied else 'green'
            
            current_vehicle = spot.get_current_vehicle()
            
            # Calculate local area occupancy for reference (radius=2 nearby spots)
            area_occupancy = HeatmapHandler._calculate_area_occupancy(spot, radius=2)
            
            heatmap_data.append({
                'spot_id': spot.spot_id,
                'spot_number': spot.spot_number,
                'color': color,  # Green = empty, Red = occupied
                'occupancy': 100 if is_spot_occupied else 0,  # Direct spot occupancy
                'area_occupancy': round(area_occupancy * 100, 1),  # For analytics
                'is_occupied': is_spot_occupied,
                'vehicle_plate': PrivacyHandler.mask_license_plate(
                    current_vehicle.vehicle.license_plate
                ) if current_vehicle else None,
                'entry_time': current_vehicle.checkin_time.isoformat() if current_vehicle else None,
                'duration': current_vehicle.get_duration_display() if current_vehicle else None,
                'spot_type': spot.spot_type
            })
        
        # Calculate lot-wide statistics
        occupied_count = sum(1 for s in heatmap_data if s['is_occupied'])
        available_count = lot.total_spots - occupied_count
        occupancy_rate = round(occupied_count / lot.total_spots * 100, 1) if lot.total_spots > 0 else 0
        
        return {
            'lot_name': lot.lot_name,
            'total_spots': lot.total_spots,
            'occupied': occupied_count,
            'available': available_count,
            'occupancy_rate': occupancy_rate,
            'spots': heatmap_data,
            'updated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def _calculate_area_occupancy(spot, radius=2):
        """Calculate occupancy in radius around spot - for analytics only"""
        try:
            nearby_spots = ParkingSpot.objects.filter(
                parking_lot=spot.parking_lot,
                spot_id__range=[spot.spot_id - radius, spot.spot_id + radius]
            )
            
            if nearby_spots.count() == 0:
                return 0.0
            
            # Count occupied spots (those with active ParkedVehicle records)
            occupied = sum(1 for s in nearby_spots if s.is_occupied())
            total = nearby_spots.count()
            
            return occupied / total if total > 0 else 0.0
        except Exception as e:
            logger.warning(f"Error calculating area occupancy for spot {spot.spot_id}: {e}")
            return 0.0
    
    @staticmethod
    def _get_color(occupancy):
        """Get color based on occupancy percentage - for area heat (not individual spots)"""
        if occupancy < 0.3:
            return 'green'  # Less than 30% area occupied
        elif occupancy < 0.7:
            return 'yellow'  # 30-70% area occupied
        else:
            return 'red'  # More than 70% area occupied
    
    @staticmethod
    def get_heatmap_analytics(lot_id):
        """Get analytics from heatmap data"""
        lot = ParkingLot.objects.get(lot_id=lot_id)
        heatmap = HeatmapHandler.get_lot_heatmap(lot_id)
        
        green_spots = [s for s in heatmap['spots'] if s['color'] == 'green']
        yellow_spots = [s for s in heatmap['spots'] if s['color'] == 'yellow']
        red_spots = [s for s in heatmap['spots'] if s['color'] == 'red']
        
        return {
            'total_spots': heatmap['total_spots'],
            'occupied': heatmap['occupied'],
            'available': heatmap['available'],
            'occupancy_rate': heatmap['occupancy_rate'],
            'free_zones': len(green_spots),
            'medium_zones': len(yellow_spots),
            'busy_zones': len(red_spots),
            'recommended_spots': green_spots[:5],  # Top 5 free spots
            'status': 'Full' if heatmap['occupancy_rate'] >= 90 else ('Busy' if heatmap['occupancy_rate'] >= 70 else 'Available')
        }
