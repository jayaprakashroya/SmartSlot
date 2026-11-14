"""
Real-Time License Plate to Parking Spot Tracking System
Maps each car's license plate to its exact parking spot location
"""

import cv2
import numpy as np
from datetime import datetime
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

class ParkingSpotTracker:
    """
    Real-time tracker that maps license plates to parking spots.
    Updates the database in real-time as vehicles are detected.
    """
    
    def __init__(self, parking_positions: List[Tuple[int, int]], frame_width: int, frame_height: int):
        """
        Initialize tracker with parking spot positions
        
        Args:
            parking_positions: List of (x, y) coordinates for each parking spot
            frame_width: Video frame width
            frame_height: Video frame height
        """
        self.parking_positions = parking_positions
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Parking spot tracking
        self.spot_assignments = {}  # spot_id -> {plate, timestamp, confidence}
        self.vehicle_history = defaultdict(list)  # plate -> list of parking events
        self.spot_occupancy = {}  # spot_id -> bool
        
        # Initialize all spots as empty
        for spot_id in range(len(parking_positions)):
            self.spot_occupancy[spot_id] = False
    
    def find_nearest_spot(self, vehicle_bbox: Tuple[int, int, int, int]) -> Tuple[int, float]:
        """
        Find the nearest parking spot to a detected vehicle.
        
        Args:
            vehicle_bbox: (x1, y1, x2, y2) bounding box of detected vehicle
            
        Returns:
            (spot_id, overlap_ratio) - nearest spot and overlap percentage
        """
        vx1, vy1, vx2, vy2 = vehicle_bbox
        vehicle_center_x = (vx1 + vx2) // 2
        vehicle_center_y = (vy1 + vy2) // 2
        
        min_distance = float('inf')
        nearest_spot_id = -1
        max_overlap = 0
        
        space_width, space_height = 107, 48
        
        for spot_id, (spot_x, spot_y) in enumerate(self.parking_positions):
            # Calculate distance from vehicle center to spot center
            spot_center_x = spot_x + space_width // 2
            spot_center_y = spot_y + space_height // 2
            
            distance = ((vehicle_center_x - spot_center_x) ** 2 + 
                       (vehicle_center_y - spot_center_y) ** 2) ** 0.5
            
            # Calculate overlap area (IoU - Intersection over Union)
            x_left = max(spot_x, vx1)
            y_top = max(spot_y, vy1)
            x_right = min(spot_x + space_width, vx2)
            y_bottom = min(spot_y + space_height, vy2)
            
            if x_right > x_left and y_bottom > y_top:
                intersection_area = (x_right - x_left) * (y_bottom - y_top)
                spot_area = space_width * space_height
                overlap_ratio = intersection_area / spot_area
                
                # Prefer spots with high overlap, but consider distance as tiebreaker
                priority = overlap_ratio - (distance / 500)  # Scale distance
                
                if overlap_ratio > max_overlap or (overlap_ratio == max_overlap and distance < min_distance):
                    max_overlap = overlap_ratio
                    min_distance = distance
                    nearest_spot_id = spot_id
        
        return nearest_spot_id, max_overlap
    
    def assign_vehicle_to_spot(self, license_plate: str, vehicle_bbox: Tuple[int, int, int, int], 
                               confidence: float) -> Dict:
        """
        Assign a detected vehicle with license plate to a parking spot.
        
        Args:
            license_plate: Extracted license plate text
            vehicle_bbox: Vehicle bounding box (x1, y1, x2, y2)
            confidence: Detection confidence score
            
        Returns:
            Assignment info: {spot_id, success, message}
        """
        if not license_plate or not license_plate.strip():
            return {'success': False, 'message': 'Invalid license plate'}
        
        spot_id, overlap = self.find_nearest_spot(vehicle_bbox)
        
        if spot_id == -1:
            return {
                'success': False,
                'message': 'No suitable parking spot found',
                'plate': license_plate
            }
        
        # If overlap is too small, don't assign
        if overlap < 0.25:  # At least 25% overlap required (stricter to avoid false positives)
            return {
                'success': False,
                'message': f'Vehicle not clearly in a spot (overlap: {overlap:.1%})',
                'plate': license_plate,
                'spot_id': spot_id,
                'overlap': overlap
            }
        
        # Remove vehicle from previous spot if it was there
        for spot, data in self.spot_assignments.items():
            if data and data.get('plate') == license_plate:
                del self.spot_assignments[spot]
        
        # Assign to new spot
        self.spot_assignments[spot_id] = {
            'plate': license_plate,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'bbox': vehicle_bbox
        }
        
        self.spot_occupancy[spot_id] = True
        
        # Record in history
        self.vehicle_history[license_plate].append({
            'event': 'parked',
            'spot_id': spot_id,
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence
        })
        
        return {
            'success': True,
            'plate': license_plate,
            'spot_id': spot_id,
            'position': self.parking_positions[spot_id],
            'overlap': overlap,
            'message': f'✅ Car {license_plate} parked at spot {spot_id + 1}'
        }
    
    def find_vehicle_spot(self, license_plate: str) -> Optional[Dict]:
        """
        Find where a vehicle with given license plate is parked.
        
        Args:
            license_plate: License plate to search for
            
        Returns:
            Parking info or None if not found
        """
        for spot_id, data in self.spot_assignments.items():
            if data and data['plate'].upper() == license_plate.upper():
                return {
                    'plate': license_plate,
                    'spot_id': spot_id,
                    'spot_number': spot_id + 1,
                    'position': self.parking_positions[spot_id],
                    'parked_at': data['timestamp'],
                    'confidence': data['confidence']
                }
        return None
    
    def get_parking_status(self) -> Dict:
        """Get current parking lot status."""
        total_spots = len(self.parking_positions)
        occupied_spots = sum(1 for v in self.spot_assignments.values() if v)
        available_spots = total_spots - occupied_spots
        
        spots_info = []
        for spot_id in range(total_spots):
            spot_data = self.spot_assignments.get(spot_id)
            spots_info.append({
                'spot_id': spot_id,
                'spot_number': spot_id + 1,
                'position': self.parking_positions[spot_id],
                'occupied': bool(spot_data),
                'vehicle': {
                    'plate': spot_data['plate'] if spot_data else None,
                    'parked_at': spot_data['timestamp'] if spot_data else None,
                    'confidence': spot_data['confidence'] if spot_data else None
                } if spot_data else None
            })
        
        return {
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots,
            'occupancy_rate': occupied_spots / total_spots if total_spots > 0 else 0,
            'spots': spots_info,
            'updated_at': datetime.now().isoformat()
        }
    
    def get_vehicle_history(self, license_plate: str) -> List[Dict]:
        """Get parking history for a vehicle."""
        return self.vehicle_history.get(license_plate, [])
    
    def visualize_parking_lot(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw parking lot with occupancy status and license plates on frame.
        
        Args:
            frame: Input video frame
            
        Returns:
            Annotated frame with parking information
        """
        annotated = frame.copy()
        space_width, space_height = 107, 48
        
        for spot_id, (spot_x, spot_y) in enumerate(self.parking_positions):
            spot_data = self.spot_assignments.get(spot_id)
            
            # Draw parking spot rectangle
            if spot_data:  # Occupied - red
                color = (0, 0, 255)
                text = f"#{spot_id + 1}\n{spot_data['plate'][:8]}"
            else:  # Available - green
                color = (0, 255, 0)
                text = f"#{spot_id + 1}\nAvailable"
            
            cv2.rectangle(annotated, (spot_x, spot_y), 
                         (spot_x + space_width, spot_y + space_height),
                         color, 2)
            
            # Add spot number and status
            cv2.putText(annotated, str(spot_id + 1), 
                       (spot_x + 10, spot_y + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            if spot_data:
                cv2.putText(annotated, spot_data['plate'][:8], 
                           (spot_x + 5, spot_y + 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        # Add summary info
        status = self.get_parking_status()
        summary = f"Occupied: {status['occupied_spots']}/{status['total_spots']} | Available: {status['available_spots']}"
        cv2.putText(annotated, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated


# Example usage demonstrating the tracker
if __name__ == "__main__":
    # Create dummy parking positions
    parking_positions = [(100 + i*120, 100 + j*60) for i in range(4) for j in range(2)]
    
    tracker = ParkingSpotTracker(parking_positions, 1280, 720)
    
    print("🅿️  Real-Time Parking Spot Tracker - Demo")
    print("=" * 50)
    
    # Simulate vehicle detections
    test_cases = [
        ("ABC-1234", (100, 100, 200, 150), 0.95),
        ("XYZ-5678", (220, 100, 320, 150), 0.92),
        ("DEF-9012", (340, 100, 440, 150), 0.88),
        ("GHI-3456", (100, 160, 200, 210), 0.91),
    ]
    
    print("\n📍 Parking Vehicles:")
    for plate, bbox, conf in test_cases:
        result = tracker.assign_vehicle_to_spot(plate, bbox, conf)
        print(f"  {result['message']}")
    
    print("\n📊 Parking Lot Status:")
    status = tracker.get_parking_status()
    print(f"  Total Spots: {status['total_spots']}")
    print(f"  Occupied: {status['occupied_spots']} | Available: {status['available_spots']}")
    print(f"  Occupancy Rate: {status['occupancy_rate']:.1%}")
    
    print("\n🔍 Find Vehicle:")
    result = tracker.find_vehicle_spot("ABC-1234")
    if result:
        print(f"  ✅ Found {result['plate']} at Spot #{result['spot_number']}")
        print(f"     Position: {result['position']}")
        print(f"     Parked at: {result['parked_at']}")
