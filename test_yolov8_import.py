#!/usr/bin/env python
"""Test YOLOv8 detector import and initialization"""

import os
import sys

# Suppress analytics
os.environ['YOLO_SUPPRESS_ANALYTICS'] = 'True'

print("[TEST] Starting YOLOv8 import test...")

try:
    print("[TEST] Step 1: Attempting to import ParkingSpaceDetector...")
    from parkingapp.yolov8_detection import ParkingSpaceDetector
    print("[SUCCESS] Import successful")
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error during import: {e}")
    sys.exit(1)

try:
    print("[TEST] Step 2: Checking if yolov8n.pt exists...")
    model_path = "yolov8n.pt"
    if os.path.exists(model_path):
        print(f"[SUCCESS] Model file exists: {model_path}")
        print(f"[INFO] File size: {os.path.getsize(model_path)} bytes")
    else:
        print(f"[WARNING] Model file not found: {model_path}")
        print(f"[INFO] YOLOv8 will attempt to download it on first use")
    
except Exception as e:
    print(f"[ERROR] Error checking model file: {e}")

print("\n[TEST] Import test completed")
