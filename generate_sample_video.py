#!/usr/bin/env python
"""Generate a sample parking lot video for testing YOLOv8 detection"""

import os
import cv2
import numpy as np
from pathlib import Path

print("[INFO] Generating sample parking lot video for testing...")

# Video settings
width, height = 1280, 720
fps = 20
duration_seconds = 10  # 10 second video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

output_path = 'media/sample_parking_lot.mp4'

# Create media folder if it doesn't exist
os.makedirs('media', exist_ok=True)

out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

if not out.isOpened():
    print(f"[ERROR] Failed to create video writer for {output_path}")
    exit(1)

print(f"[INFO] Creating video: {output_path} ({duration_seconds} seconds)")

# Frame-by-frame generation
total_frames = fps * duration_seconds

for frame_idx in range(total_frames):
    # Create frame background (parking lot asphalt)
    frame = np.ones((height, width, 3), dtype=np.uint8)
    
    # Asphalt color (gray)
    frame[:] = (100, 100, 100)
    
    # Add parking lot lines (white horizontal and vertical lines)
    line_thickness = 3
    line_color = (255, 255, 255)
    
    # Vertical parking space lines
    for x in range(0, width, 160):
        cv2.line(frame, (x, 0), (x, height), line_color, line_thickness)
    
    # Horizontal lines
    for y in range(0, height, 120):
        cv2.line(frame, (0, y), (width, y), line_color, line_thickness)
    
    # Add some parked cars (as rectangles) - static positions
    parked_cars = [
        ((100, 150), (200, 250), (0, 0, 255)),      # Red car
        ((350, 150), (450, 250), (0, 255, 0)),      # Green car
        ((600, 150), (700, 250), (255, 0, 0)),      # Blue car
        ((100, 350), (200, 450), (0, 255, 255)),    # Yellow car
        ((900, 200), (1000, 300), (255, 0, 255)),   # Magenta car
    ]
    
    for (x1, y1), (x2, y2), color in parked_cars:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        # Add a small window detail
        cv2.rectangle(frame, (x1 + 10, y1 + 10), (x1 + 30, y1 + 30), (200, 200, 200), -1)
    
    # Add moving car (animated)
    # Car moves left to right across the video
    car_x = int((frame_idx / total_frames) * (width - 150))
    car_y = 550
    car_color = (0, 165, 255)  # Orange
    
    cv2.rectangle(frame, (car_x, car_y), (car_x + 150, car_y + 80), car_color, -1)
    # Add windows
    cv2.rectangle(frame, (car_x + 20, car_y + 15), (car_x + 50, car_y + 40), (200, 200, 200), -1)
    cv2.rectangle(frame, (car_x + 80, car_y + 15), (car_x + 110, car_y + 40), (200, 200, 200), -1)
    # Add wheels
    cv2.circle(frame, (car_x + 40, car_y + 75), 12, (50, 50, 50), -1)
    cv2.circle(frame, (car_x + 120, car_y + 75), 12, (50, 50, 50), -1)
    
    # Add some text info
    cv2.putText(frame, f"Frame: {frame_idx + 1}/{total_frames}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Sample Parking Lot - YOLOv8 Test Video", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Add parking status
    occupied = len(parked_cars)
    total_spaces = 8
    cv2.putText(frame, f"Occupied: {occupied}/{total_spaces} spaces", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # Write frame to video
    out.write(frame)
    
    # Print progress
    if (frame_idx + 1) % 20 == 0:
        print(f"  Progress: {frame_idx + 1}/{total_frames} frames")

out.release()

print(f"[SUCCESS] Video generated successfully!")
print(f"[INFO] Video saved to: {output_path}")
print(f"[INFO] Video resolution: {width}x{height}")
print(f"[INFO] Video FPS: {fps}")
print(f"[INFO] Duration: {duration_seconds} seconds")
print(f"[INFO] Total frames: {total_frames}")
print(f"\n[NEXT] Upload this video to test YOLOv8 detection at: http://127.0.0.1:8000/smartcarpaking/")
