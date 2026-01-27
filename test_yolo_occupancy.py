"""
Test script to diagnose YOLO occupancy detection issue
Check if vehicles are being detected and marked as occupied
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartparking.settings')

import django
django.setup()

import cv2
import numpy as np
from parkingapp.yolov8_detection import ParkingSpaceDetector

# Create test parking positions (simulating 10 spots in a grid)
parking_positions = [
    (50, 50), (160, 50), (270, 50),
    (50, 110), (160, 110), (270, 110),
    (50, 170), (160, 170), (270, 170),
    (50, 230)
]

print("=" * 70)
print("YOLO OCCUPANCY DETECTION DIAGNOSTIC")
print("=" * 70)

# Test 1: Create empty frame
print("\n[TEST 1] Empty parking lot (all green)")
print("-" * 70)
frame = np.zeros((400, 500, 3), dtype=np.uint8)
frame[:, :] = (100, 100, 100)  # Gray background

detector = ParkingSpaceDetector(model_name='yolov8n.pt')
detections = detector.detect_vehicles(frame, conf_threshold=0.5)
results = detector.analyze_parking_space(frame, parking_positions, detections)

print(f"Vehicle detections: {len(detections)}")
print(f"Available spots: {results['statistics']['available_count']}")
print(f"Occupied spots: {results['statistics']['occupied_count']}")
print(f"Occupancy rate: {results['statistics']['occupancy_rate']:.1f}%")

# Test 2: Create frame with drawn vehicles (simulated)
print("\n[TEST 2] Occupied parking lot (should have red spots)")
print("-" * 70)
frame = np.zeros((400, 500, 3), dtype=np.uint8)
frame[:, :] = (100, 100, 100)  # Gray background

# Draw blue rectangles as fake vehicles on some spots
for i, (x, y) in enumerate(parking_positions[:4]):
    # Draw a vehicle (blue rectangle) slightly larger than parking spot
    cv2.rectangle(frame, (x-5, y-5), (x+112, y+53), (255, 0, 0), -1)  # Filled blue
    print(f"  Drew vehicle on spot {i+1} at ({x}, {y})")

print(f"\nFrame content: Background gray (100,100,100), Vehicles blue (255,0,0)")

detections = detector.detect_vehicles(frame, conf_threshold=0.25)
print(f"Vehicle detections found: {len(detections)}")
for i, det in enumerate(detections):
    print(f"  Detection {i+1}: {det['class']} at {det['bbox']} (conf: {det['confidence']:.2f})")

results = detector.analyze_parking_space(frame, parking_positions, detections)

print(f"\nOccupancy Analysis:")
print(f"  Available spots: {results['statistics']['available_count']}")
print(f"  Occupied spots: {results['statistics']['occupied_count']}")
print(f"  Occupancy rate: {results['statistics']['occupancy_rate']:.1f}%")

# Show which spots are marked as occupied
print(f"\nOccupied spot details:")
if results['occupied']:
    for i, space in enumerate(results['occupied']):
        print(f"  Spot {i+1}: pos={space['position']}, conf={space['confidence']:.2f}")
else:
    print("  ❌ NO OCCUPIED SPOTS DETECTED!")

# Show which spots are marked as available
print(f"\nAvailable spot details (first 3):")
for i, space in enumerate(results['available'][:3]):
    print(f"  Spot {i+1}: pos={space['position']}, conf={space['confidence']:.2f}")

# Test 3: Check overlap calculation directly
print("\n[TEST 3] Direct overlap calculation")
print("-" * 70)

parking_x, parking_y = 50, 50
space_width, space_height = 107, 48

# Vehicle (blue rectangle) from test 2
vehicle_bbox = (45, 45, 155, 103)  # Overlaps with first parking spot
vx1, vy1, vx2, vy2 = vehicle_bbox
px1, py1 = parking_x, parking_y
px2, py2 = parking_x + space_width, parking_y + space_height

print(f"Parking space: ({px1}, {py1}) to ({px2}, {py2})")
print(f"Vehicle bbox: ({vx1}, {vy1}) to ({vx2}, {vy2})")

# Calculate overlap
x_left = max(px1, vx1)
y_top = max(py1, vy1)
x_right = min(px2, vx2)
y_bottom = min(py2, vy2)

if x_right > x_left and y_bottom > y_top:
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    space_area = space_width * space_height
    overlap_ratio = intersection_area / space_area
    print(f"Intersection area: {intersection_area}")
    print(f"Space area: {space_area}")
    print(f"Overlap ratio: {overlap_ratio:.2%}")
    print(f"Threshold: 30%")
    print(f"Result: {'✅ OCCUPIED' if overlap_ratio > 0.30 else '❌ AVAILABLE'}")
else:
    print("❌ No intersection detected!")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
