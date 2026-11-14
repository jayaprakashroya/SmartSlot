"""
Quick test to verify YOLO vehicle detection
Doesn't require Django - just tests the detector directly
"""
from parkingapp.yolov8_detection import ParkingSpaceDetector

print("=" * 70)
print("YOLO VEHICLE DETECTION TEST")
print("=" * 70)

# Initialize detector
print("\n[1] Initializing YOLOv8 detector...")
try:
    detector = ParkingSpaceDetector(model_name='yolov8n.pt')
    print("    ✅ Detector initialized successfully")
except Exception as e:
    print(f"    ❌ Failed to initialize: {e}")
    exit(1)

# Test with webcam/video
print("\n[2] Testing with video source...")
print("    This will capture 3 frames from your camera/video")

import cv2
import time

# Try to open webcam or first video source
cap = cv2.VideoCapture(0)  # 0 = webcam, or provide path to video file

if not cap.isOpened():
    print("    ⚠️  Cannot open webcam. Trying alternative...")
    # Try file
    cap = cv2.VideoCapture('sample_video.mp4')
    if not cap.isOpened():
        print("    ❌ No video source available")
        exit(1)

print("    ✅ Video source opened")

# Capture and test 3 frames
frame_count = 0
max_frames = 3
detection_counts = []

print(f"\n[3] Processing frames...")
while frame_count < max_frames:
    ret, frame = cap.read()
    if not ret:
        print("    ⚠️  End of video reached")
        break
    
    frame_count += 1
    
    # Detect vehicles
    detections = detector.detect_vehicles(frame, conf_threshold=0.25)
    detection_counts.append(len(detections))
    
    print(f"    Frame {frame_count}: {len(detections)} vehicles detected", end="")
    if len(detections) > 0:
        print(" ✅")
        for i, det in enumerate(detections[:2]):  # Show first 2
            print(f"      {i+1}. {det['class']:10s} - Confidence: {det['confidence']:.1%}")
        if len(detections) > 2:
            print(f"      ... and {len(detections) - 2} more")
    else:
        print(" (empty scene)")

cap.release()

# Summary
print(f"\n[4] SUMMARY")
print(f"    Frames analyzed: {len(detection_counts)}")
print(f"    Average detections: {sum(detection_counts) / len(detection_counts):.1f}")

if sum(detection_counts) > 0:
    print("\n    ✅ Vehicle detection is WORKING!")
    print("    If occupied spots still show green:")
    print("       - Check parking position file matches video resolution")
    print("       - Lower overlap threshold in yolov8_detection.py")
else:
    print("\n    ⚠️  No vehicles detected!")
    print("    Possible causes:")
    print("       - Empty/sparse scenes")
    print("       - Poor lighting")
    print("       - Vehicles too small or far")
    print("       - Model needs tuning")
    print("\n    Try:")
    print("       - Lower conf_threshold to 0.15")
    print("       - Use yolov8m model instead of yolov8n")

print("\n" + "=" * 70)
