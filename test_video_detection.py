#!/usr/bin/env python
"""Test YOLOv8 detection on actual video file"""

import os
import sys
import cv2
import pickle

# Suppress analytics
os.environ['YOLO_SUPPRESS_ANALYTICS'] = 'True'

print("[TEST] Starting YOLOv8 video detection test...")

try:
    print("[TEST] Step 1: Finding video file...")
    video_file = None
    media_dir = 'media'
    
    if os.path.exists(media_dir):
        for file in os.listdir(media_dir):
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_file = os.path.join(media_dir, file)
                print(f"[SUCCESS] Found video: {video_file}")
                break
    
    if not video_file:
        print("[WARNING] No video file found, creating a test video with synthetic frames...")
        # Create a dummy video to test
        import numpy as np
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('test_video.mp4', fourcc, 20.0, (640, 480))
        
        # Generate 50 dummy frames
        for i in range(50):
            frame_intensity = ((i * 5) % 255)
            dummy_frame = np.full((480, 640, 3), frame_intensity * 0.3 + 100, dtype=np.uint8)
            out.write(dummy_frame)
        
        out.release()
        video_file = 'test_video.mp4'
        print(f"[SUCCESS] Created test video: {video_file}")
    
    print(f"[TEST] Step 2: Loading video - {video_file}...")
    cap = cv2.VideoCapture(video_file)
    
    if not cap.isOpened():
        print(f"[ERROR] Failed to open video file: {video_file}")
        sys.exit(1)
    
    print(f"[SUCCESS] Video opened successfully!")
    
    print("[TEST] Step 3: Loading parking positions...")
    pos_file = 'parkingapp/CarParkPos'
    if not os.path.exists(pos_file):
        print(f"[WARNING] Parking positions file not found: {pos_file}")
        print("[INFO] Creating dummy parking positions...")
        posList = [(100 + i*120, 100 + j*60) for i in range(4) for j in range(2)]
        print(f"[SUCCESS] Created {len(posList)} dummy parking positions")
    else:
        with open(pos_file, 'rb') as f:
            posList = pickle.load(f)
        print(f"[SUCCESS] Loaded {len(posList)} parking positions")
    
    print("[TEST] Step 4: Importing detector...")
    from parkingapp.yolov8_detection import ParkingSpaceDetector
    
    print("[TEST] Step 5: Initializing detector...")
    detector = ParkingSpaceDetector(model_name='yolov8n.pt')
    print("[SUCCESS] Detector initialized!")
    
    print("[TEST] Step 6: Processing first 5 frames...")
    frame_count = 0
    detection_count = 0
    
    while cap.isOpened() and frame_count < 5:
        success, frame = cap.read()
        if not success:
            break
        
        print(f"\n[PROCESSING] Frame {frame_count + 1}...")
        print(f"  Frame shape: {frame.shape}")
        
        # Detect vehicles
        detections = detector.detect_vehicles(frame, conf_threshold=0.5)
        print(f"  Detections found: {len(detections)}")
        
        for i, det in enumerate(detections):
            print(f"    - Detection {i+1}: {det['class']} (confidence: {det['confidence']:.2f})")
            detection_count += 1
        
        # Analyze parking spaces
        results = detector.analyze_parking_space(frame, posList, detections)
        print(f"  Parking spaces: {results['statistics']['total_spaces']}")
        print(f"    - Available: {results['statistics']['available_count']}")
        print(f"    - Occupied: {results['statistics']['occupied_count']}")
        print(f"    - Occupancy rate: {results['statistics']['occupancy_rate']:.1%}")
        
        frame_count += 1
    
    cap.release()
    
    print(f"\n[SUCCESS] Video processing test complete!")
    print(f"  Total frames processed: {frame_count}")
    print(f"  Total detections: {detection_count}")
    print(f"  Average detections per frame: {detection_count / max(frame_count, 1):.2f}")
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
