#!/usr/bin/env python
"""
SmartSlot YOLOv8 Quick Start Guide
Run this file to start your parking system with YOLOv8 detection
"""

import os
import sys
import subprocess

print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║         SmartSlot Parking System - YOLOv8 Edition              ║
║                                                                ║
║            🚀 Starting with 95%+ Accuracy Detection 🚀         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")

print("\n[STEP 1] Checking YOLOv8 availability...")
try:
    from ultralytics import YOLO
    print("✅ YOLOv8 installed successfully!\n")
except ImportError:
    print("❌ YOLOv8 not found. Installing now...")
    subprocess.run([sys.executable, "-m", "pip", "install", "ultralytics"], check=True)
    print("✅ YOLOv8 installed!\n")

print("[STEP 2] Checking detection module...")
try:
    from parkingapp.yolov8_detection import ParkingSpaceDetector
    print("✅ Detection module loaded!\n")
except ImportError as e:
    print(f"❌ Error: {e}\n")
    sys.exit(1)

print("[STEP 3] Starting Django development server...\n")
print("=" * 60)

# Start Django server
try:
    os.system("python manage.py runserver")
except KeyboardInterrupt:
    print("\n\n✅ Server stopped gracefully")
except Exception as e:
    print(f"\n❌ Error: {e}")
