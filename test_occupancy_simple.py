"""
Simple YOLO occupancy detection diagnostic (no Django required)
Check if vehicles are being detected and marked as occupied
"""
import cv2
import numpy as np
import sys
import os

# Add the parking app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parkingapp.yolov8_detection import ParkingSpaceDetector

# Create test parking positions
parking_positions = [
    (50, 50), (160, 50), (270, 50),
    (50, 110), (160, 110), (270, 110),
    (50, 170), (160, 170), (270, 170),
    (50, 230)
]

print("=" * 70)
print("YOLO OCCUPANCY DETECTION DIAGNOSTIC")
print("=" * 70)

# Test 1: Empty frame
print("\n[TEST 1] Empty parking lot (should be all green)")
print("-" * 70)
frame = np.ones((400, 500, 3), dtype=np.uint8) * 100  # Gray background

detector = ParkingSpaceDetector(model_name='yolov8n.pt')
print(f"Detector initialized")

detections = detector.detect_vehicles(frame, conf_threshold=0.25)
results = detector.analyze_parking_space(frame, parking_positions, detections)

print(f"Vehicle detections: {len(detections)}")
print(f"Available spots: {results['statistics']['available_count']}")
print(f"Occupied spots: {results['statistics']['occupied_count']}")
print(f"Occupancy rate: {results['statistics']['occupancy_rate']:.1f}%")
print(f"Expected: 10 available, 0 occupied")
print(f"Result: {'✅ PASS' if results['statistics']['occupied_count'] == 0 else '❌ FAIL'}")

# Test 2: Frame with vehicles (draw blue rectangles to simulate parked cars)
print("\n[TEST 2] With vehicles on some spots (should be red)")
print("-" * 70)
frame = np.ones((400, 500, 3), dtype=np.uint8) * 100  # Gray background

# Draw blue rectangles as fake vehicles on first 4 spots
for i in range(4):
    x, y = parking_positions[i]
    # Draw vehicle overlapping parking space
    cv2.rectangle(frame, (x-5, y-5), (x+112, y+53), (255, 0, 0), -1)
    print(f"  Drew vehicle on spot {i+1}")

detections = detector.detect_vehicles(frame, conf_threshold=0.25)
print(f"\nVehicle detections found: {len(detections)}")

results = detector.analyze_parking_space(frame, parking_positions, detections)

print(f"\nOccupancy Analysis:")
print(f"  Available: {results['statistics']['available_count']}")
print(f"  Occupied: {results['statistics']['occupied_count']}")
print(f"  Occupancy rate: {results['statistics']['occupancy_rate']:.1f}%")
print(f"  Detection confidence: {results['statistics']['detection_confidence']:.1%}")

print(f"\nExpected: 6 available (spots 5-10), 4 occupied (spots 1-4)")
result = (results['statistics']['occupied_count'] == 4 and 
          results['statistics']['available_count'] == 6)
print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")

if results['statistics']['occupied_count'] != 4:
    print(f"\n⚠️  Problem: Expected 4 occupied but got {results['statistics']['occupied_count']}")
    print("   Possible causes:")
    print("   1. YOLOv8 not detecting blue rectangles as vehicles")
    print("   2. Overlap threshold (30%) might be too high")
    print("   3. Vehicle detection confidence threshold too high")

# Test 3: Check drawing
print("\n[TEST 3] Draw results on frame")
print("-" * 70)
frame_drawn = detector.draw_results(frame.copy(), results)
print(f"Frame with results drawn: {frame_drawn.shape}")
print(f"Green pixels (available): {np.sum((frame_drawn[:,:,1] == 255) & (frame_drawn[:,:,0:1] < 100) & (frame_drawn[:,:,2:3] < 100))}")
print(f"Red pixels (occupied): {np.sum((frame_drawn[:,:,2] == 255) & (frame_drawn[:,:,0:1] < 100) & (frame_drawn[:,:,1:2] < 100))}")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
