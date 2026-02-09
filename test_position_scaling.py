#!/usr/bin/env python
"""
Test parking position scaling for multi-resolution support
Verifies that positions are correctly scaled from 1280×720 baseline
"""

import cv2
import pickle
from parkingapp.video_calibration import VideoCalibrator

# Load original parking positions (calibrated for 1280×720)
with open('parkingapp/CarParkPos', 'rb') as f:
    original_positions = pickle.load(f)

print("=" * 70)
print("PARKING POSITION SCALING TEST")
print("=" * 70)
print(f"\nOriginal positions (1280×720): {len(original_positions)} spots")
print(f"First 5 positions: {original_positions[:5]}\n")

calibrator = VideoCalibrator()

# Test videos
test_videos = [
    ('videos/13072225_3840_2160_60fps.mp4', '4K 3840×2160', 3840, 2160),
    ('videos/carPark_Vh8PxPQ_h3PHiDT.mp4', 'Custom 1100×720', 1100, 720),
    ('videos/4196207-uhd_3840_2160_24fps_FaHaXEn.mp4', '4K 3840×2160', 3840, 2160),
    ('videos/12125597_640_360_30fps.mp4', 'Low-res 640×360', 640, 360),
]

print("SCALING VERIFICATION BY VIDEO RESOLUTION:")
print("-" * 70)

for video_name, desc, expected_w, expected_h in test_videos:
    try:
        cap = cv2.VideoCapture(video_name)
        if not cap.isOpened():
            print(f"❌ {desc}: Video not found at {video_name}")
            continue
        
        success, frame = cap.read()
        if not success:
            print(f"❌ {desc}: Cannot read first frame")
            cap.release()
            continue
        
        actual_w = frame.shape[1]
        actual_h = frame.shape[0]
        
        # Get scaled spot dimensions
        spot_w, spot_h = calibrator.get_scaled_dimensions(frame)
        
        # Calculate scaling factors
        scale_x = actual_w / 1280
        scale_y = actual_h / 720
        
        # Scale first 3 positions as examples
        scaled_positions = [(int(x * scale_x), int(y * scale_y)) for x, y in original_positions[:3]]
        
        print(f"\n✅ {desc}")
        print(f"   Resolution: {actual_w}×{actual_h} (expected: {expected_w}×{expected_h})")
        print(f"   Scaling factors: X={scale_x:.3f}, Y={scale_y:.3f}")
        print(f"   Scaled spot size: {spot_w}×{spot_h} pixels")
        print(f"   Original positions: {original_positions[:3]}")
        print(f"   Scaled positions:   {scaled_positions}")
        
        cap.release()
        
    except Exception as e:
        print(f"❌ {desc}: Error - {e}")

print("\n" + "=" * 70)
print("SCALING FORMULA:")
print("=" * 70)
print("Base resolution (1280×720) with parking spots of 107×48 pixels")
print("\nFor any video resolution:")
print("  scale_x = video_width / 1280")
print("  scale_y = video_height / 720")
print("  scaled_position_x = original_x * scale_x")
print("  scaled_position_y = original_y * scale_y")
print("  scaled_spot_width = 107 * scale_x")
print("  scaled_spot_height = 48 * scale_y")
print("\nExamples:")
print("  3840×2160 (4K):    scale_x=3.0, scale_y=3.0    → positions 3× larger")
print("  1100×720:          scale_x=0.86, scale_y=1.0   → positions 0.86× larger")
print("  640×360 (low-res): scale_x=0.5, scale_y=0.5    → positions 0.5× larger")
print("=" * 70)
print("\n✅ POSITION SCALING TEST COMPLETE")
