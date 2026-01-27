#!/usr/bin/env python
"""Test YOLO model initialization and detection"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

print("=" * 70)
print("YOLO MODEL DIAGNOSTICS")
print("=" * 70)

# Test 1: Check ultralytics installation
print("\n[TEST 1] Checking ultralytics (YOLOv8)...")
try:
    from ultralytics import YOLO
    print("✅ YOLO imported successfully")
except Exception as e:
    print(f"❌ Error importing YOLO: {e}")
    sys.exit(1)

# Test 2: Check detection module
print("\n[TEST 2] Checking yolov8_detection.py...")
try:
    from parkingapp.yolov8_detection import ParkingSpaceDetector
    print("✅ ParkingSpaceDetector class imported")
except Exception as e:
    print(f"❌ Error importing ParkingSpaceDetector: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Initialize detector
print("\n[TEST 3] Initializing detector...")
try:
    detector = ParkingSpaceDetector(model_name='yolov8n.pt')
    print("✅ Detector initialized successfully")
except Exception as e:
    print(f"❌ Error initializing detector: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check methods
print("\n[TEST 4] Checking detector methods...")
try:
    methods = ['detect_vehicles', 'analyze_parking_space', 'draw_results']
    for method in methods:
        if hasattr(detector, method):
            print(f"✅ Method '{method}' exists")
        else:
            print(f"❌ Method '{method}' missing")
except Exception as e:
    print(f"❌ Error checking methods: {e}")

# Test 5: Test detection on dummy frame
print("\n[TEST 5] Testing detection on dummy frame...")
try:
    import numpy as np
    import cv2
    
    # Create dummy frame
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Test detection
    detections = detector.detect_vehicles(dummy_frame)
    print(f"✅ Detection ran successfully (found {len(detections)} vehicles in blank frame)")
    
    # Test parking space analysis
    parking_positions = [(100, 100), (200, 100), (300, 100)]
    results = detector.analyze_parking_space(dummy_frame, parking_positions, detections)
    print(f"✅ Parking space analysis completed")
    print(f"   - Available: {results['statistics']['available_count']}")
    print(f"   - Occupied: {results['statistics']['occupied_count']}")
    
except Exception as e:
    print(f"❌ Error testing detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Check views integration
print("\n[TEST 6] Checking views.py integration...")
try:
    from parkingapp.views import YOLOV8_AVAILABLE, get_yolo_detector
    print(f"✅ Views imported successfully")
    print(f"   - YOLOV8_AVAILABLE: {YOLOV8_AVAILABLE}")
    
    detector_from_views = get_yolo_detector()
    if detector_from_views:
        print(f"✅ get_yolo_detector() returned detector instance")
    else:
        print(f"⚠️  get_yolo_detector() returned None")
        
except Exception as e:
    print(f"❌ Error in views integration: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("YOLO MODEL DIAGNOSTICS COMPLETE")
print("=" * 70)
