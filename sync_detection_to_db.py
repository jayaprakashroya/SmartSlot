#!/usr/bin/env python
"""
Sync YOLOv8 Detection Results Directly to Database
This script ensures detection results are saved to update heatmap colors
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.utils import timezone
from parkingapp.models import ParkingSpot, ParkedVehicle, Vehicle, ParkingLot
import logging

logger = logging.getLogger(__name__)

class DetectionSyncManager:
    """Sync detection results to database"""
    
    @staticmethod
    def sync_spot_detections(lot_id, spot_detections):
        """
        Sync spot detection results to database.
        
        Args:
            lot_id: Parking lot ID
            spot_detections: Dict of {spot_id: {'occupied': bool, 'plate': str, 'confidence': float}}
        """
        try:
            lot = ParkingLot.objects.get(lot_id=lot_id)
            updated = {'occupied': 0, 'empty': 0, 'errors': 0}
            
            for spot_id_str, detection in spot_detections.items():
                try:
                    spot_id = int(spot_id_str)
                    spot = ParkingSpot.objects.get(spot_id=spot_id)
                    
                    is_occupied = detection.get('occupied', False)
                    plate = detection.get('plate', f'DETECTED_{spot_id}')
                    confidence = detection.get('confidence', 0.0)
                    
                    # Get active parking record
                    active = ParkedVehicle.objects.filter(
                        parking_spot=spot,
                        checkout_time__isnull=True
                    ).first()
                    
                    if is_occupied:
                        # Mark as occupied
                        if not active:
                            # Create new record
                            vehicle, _ = Vehicle.objects.get_or_create(
                                license_plate=plate,
                                defaults={'vehicle_type': 'car', 'color': 'unknown'}
                            )
                            
                            ParkedVehicle.objects.create(
                                vehicle=vehicle,
                                parking_spot=spot,
                                checkin_time=timezone.now(),
                                detection_confidence=confidence
                            )
                            
                            logger.info(f"✓ Spot {spot.spot_number}: OCCUPIED")
                            updated['occupied'] += 1
                        else:
                            # Update confidence
                            active.detection_confidence = confidence
                            active.save()
                            updated['occupied'] += 1
                    else:
                        # Mark as empty
                        if active:
                            active.checkout_time = timezone.now()
                            active.save()
                            logger.info(f"✓ Spot {spot.spot_number}: EMPTY")
                            updated['empty'] += 1
                        else:
                            updated['empty'] += 1
                            
                except (ValueError, ParkingSpot.DoesNotExist) as e:
                    logger.error(f"✗ Spot {spot_id_str}: {e}")
                    updated['errors'] += 1
                except Exception as e:
                    logger.error(f"✗ Error updating spot {spot_id_str}: {e}")
                    updated['errors'] += 1
            
            logger.info(f"Sync Complete: {updated['occupied']} occupied, {updated['empty']} empty, {updated['errors']} errors")
            return updated
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {'occupied': 0, 'empty': 0, 'errors': 1}
    
    @staticmethod
    def clear_old_detections(hours=2):
        """Clear old detection records older than N hours"""
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            
            # Find old parking records without checkout times (over N hours old)
            old_records = ParkedVehicle.objects.filter(
                checkin_time__lt=cutoff_time,
                checkout_time__isnull=True
            )
            
            count = old_records.count()
            if count > 0:
                old_records.update(checkout_time=timezone.now())
                logger.info(f"Cleared {count} stale detection records")
            
            return count
            
        except Exception as e:
            logger.error(f"Error clearing old detections: {e}")
            return 0
    
    @staticmethod
    def get_heatmap_status(lot_id):
        """Get current heatmap status from database"""
        try:
            lot = ParkingLot.objects.get(lot_id=lot_id)
            spots = lot.spots.all()
            
            occupied_count = 0
            empty_count = 0
            spot_details = []
            
            for spot in spots:
                is_occupied = spot.is_occupied()
                
                if is_occupied:
                    occupied_count += 1
                    color = 'red'
                    vehicle = spot.get_current_vehicle()
                    plate = vehicle.vehicle.license_plate if vehicle else 'Unknown'
                else:
                    empty_count += 1
                    color = 'green'
                    plate = None
                
                spot_details.append({
                    'spot_id': spot.spot_id,
                    'spot_number': spot.spot_number,
                    'color': color,
                    'occupied': is_occupied,
                    'plate': plate
                })
            
            occupancy_rate = (occupied_count / (occupied_count + empty_count) * 100) if (occupied_count + empty_count) > 0 else 0
            
            return {
                'lot_id': lot_id,
                'lot_name': lot.lot_name,
                'total': occupied_count + empty_count,
                'occupied': occupied_count,
                'empty': empty_count,
                'occupancy_rate': round(occupancy_rate, 1),
                'spots': spot_details,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting heatmap status: {e}")
            return None


def main():
    """Test the sync manager"""
    import json
    
    print("\n" + "="*70)
    print("DETECTION SYNC TO DATABASE TEST")
    print("="*70)
    
    # Get first parking lot
    try:
        lot = ParkingLot.objects.first()
        if not lot:
            print("❌ No parking lot found. Create a parking lot first.")
            return
        
        lot_id = lot.lot_id
        print(f"\n✓ Using Parking Lot: {lot.lot_name} (ID: {lot_id})")
        
        # Show current status
        print("\n" + "-"*70)
        print("CURRENT HEATMAP STATUS")
        print("-"*70)
        
        status = DetectionSyncManager.get_heatmap_status(lot_id)
        if status:
            print(f"Total Spots: {status['total']}")
            print(f"Occupied (Red): {status['occupied']}")
            print(f"Empty (Green): {status['empty']}")
            print(f"Occupancy Rate: {status['occupancy_rate']}%")
            
            print("\nSample Spots:")
            for spot in status['spots'][:10]:
                color_emoji = "🔴" if spot['color'] == 'red' else "🟢"
                print(f"  {color_emoji} {spot['spot_number']}: {spot['color'].upper()} - Plate: {spot['plate']}")
        
        # Test sync with sample data
        print("\n" + "-"*70)
        print("TEST SYNC WITH SAMPLE DATA")
        print("-"*70)
        
        # Create sample detections (50% occupied)
        spots = list(lot.spots.all()[:10])
        sample_detections = {}
        
        for i, spot in enumerate(spots):
            is_occupied = (i % 2 == 0)  # Alternate occupied/empty
            sample_detections[str(spot.spot_id)] = {
                'occupied': is_occupied,
                'plate': f'ABC-{i:03d}' if is_occupied else None,
                'confidence': 0.85 if is_occupied else 0.0
            }
        
        result = DetectionSyncManager.sync_spot_detections(lot_id, sample_detections)
        print(f"\n✓ Sync Result: {result}")
        
        # Show updated status
        print("\n" + "-"*70)
        print("UPDATED HEATMAP STATUS")
        print("-"*70)
        
        status = DetectionSyncManager.get_heatmap_status(lot_id)
        if status:
            print(f"Occupied (Red): {status['occupied']}")
            print(f"Empty (Green): {status['empty']}")
            print(f"Occupancy Rate: {status['occupancy_rate']}%")
        
        print("\n" + "="*70)
        print("✅ SYNC TEST COMPLETE")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    main()
