#!/usr/bin/env python
"""Test YOLOv8 detector actual initialization"""

import os
import sys
import numpy as np
import cv2

# Suppress analytics
os.environ['YOLO_SUPPRESS_ANALYTICS'] = 'True'

print("[TEST] Starting YOLOv8 detector initialization test...")

try:
    print("[TEST] Step 1: Importing detector...")
    from parkingapp.yolov8_detection import ParkingSpaceDetector
    print("[SUCCESS] Import successful")
    
    print("[TEST] Step 2: Initializing detector with model...")
    detector = ParkingSpaceDetector(model_name='yolov8n.pt')
    print("[SUCCESS] Detector initialized!")
    
    print("[TEST] Step 3: Testing detection with dummy frame...")
    # Create a dummy frame (3-channel BGR image)
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    detections = detector.detect_vehicles(dummy_frame, conf_threshold=0.5)
    print(f"[SUCCESS] detect_vehicles() ran successfully! Found {len(detections)} detections")
    
    print("[TEST] Step 4: Testing analyze_parking_space...")
    parking_positions = [(100, 100), (220, 100), (340, 100)]
    results = detector.analyze_parking_space(dummy_frame, parking_positions, detections)
    print(f"[SUCCESS] analyze_parking_space() ran successfully!")
    print(f"[INFO] Result keys: {results.keys()}")
    
    print("[TEST] Step 5: Testing draw_results...")
    annotated = detector.draw_results(dummy_frame.copy(), results)
    print(f"[SUCCESS] draw_results() ran successfully! Output shape: {annotated.shape}")
    
    print("\n[SUCCESS] All detector methods work!")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
