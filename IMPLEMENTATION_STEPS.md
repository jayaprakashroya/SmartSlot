"""
IMPLEMENTATION EXAMPLE: Integrating Adaptive Detection into views.py
=====================================================================

This file shows the EXACT code changes needed to enable adaptive
threshold detection in your existing Django views.

Two options are provided:
1. OPTION A: Replace generate_frames() with adaptive version
2. OPTION B: Minimal changes to existing code
"""

# ═══════════════════════════════════════════════════════════════════
# OPTION A: COMPLETE REPLACEMENT (recommended)
# ═══════════════════════════════════════════════════════════════════
"""
Replace the entire generate_frames() function in views.py with this:
"""

OPTION_A_CODE = '''
def generate_frames(cap, posList, detection_type='multi_lane'):
    """
    Parking space detection with ADAPTIVE threshold calibration.
    Replaces hardcoded 900 threshold with intelligent auto-tuning.
    """
    from parkingapp.adaptive_detection import (
        AdaptiveThresholdCalculator,
        AdaptiveDetector,
        VideoResolutionAdapter
    )
    
    # Get video properties
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"[INFO] Processing video: {video_width}x{video_height}")
    
    # Get adaptive parking space size based on resolution
    width, height = VideoResolutionAdapter.get_parking_space_size(
        (video_width, video_height)
    )
    
    # Step 1: Calibrate optimal threshold from sample frames
    print(f"[INFO] Calibrating threshold from 20 sample frames...")
    calculator = AdaptiveThresholdCalculator(sample_frame_count=20)
    calibration = calculator.analyze_sample_frames(cap, posList, width, height)
    base_threshold = calibration['optimal_threshold']
    
    print(f"[CALIBRATION RESULTS]")
    print(f"  Optimal Threshold: {base_threshold}")
    print(f"  Mean Empty: {calibration['mean_empty']}")
    print(f"  Mean Occupied: {calibration['mean_occupied']}")
    print(f"  Standard Deviation: {calibration['std_dev']:.1f}")
    print(f"  Parking Space Size: {width}x{height} pixels")
    print(f"  Brightness: {calibration['brightness_avg']:.1f}/255")
    
    # Step 2: Create adaptive detector for runtime threshold adjustments
    adaptive_detector = AdaptiveDetector(base_threshold=base_threshold)
    frame_counter = 0
    recalibration_interval = 500  # Recalibrate every 500 frames if needed
    
    def check_parking_space(img_pro, img, current_frame=None):
        nonlocal frame_counter
        space_counter = 0
        
        # Update adaptive threshold every 5 frames
        if frame_counter % 5 == 0 and current_frame is not None:
            current_threshold = adaptive_detector.get_adaptive_threshold(current_frame)
        else:
            current_threshold = adaptive_detector.last_threshold
        
        # Process each parking space
        for pos in posList:
            x, y = pos
            img_crop = img_pro[y:y + height, x:x + width]
            count = cv2.countNonZero(img_crop)
            
            # ADAPTIVE THRESHOLD (was: if count < 900)
            if count < current_threshold:
                color = (0, 255, 0)  # GREEN = FREE/VACANT
                thickness = 5
                space_counter += 1
            else:
                color = (0, 0, 255)  # RED = OCCUPIED
                thickness = 2
            
            # Draw detection results
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
            cvzone.putTextRect(img, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)
        
        # Display statistics
        detection_info = {
            'multi_lane': 'Multi-Lane Detection (Adaptive)',
            'reserved_spot': 'Reserved Spot (Adaptive)',
            'night_vision': 'Night Vision (Adaptive)',
            'angled_spot': 'Angled Spot (Adaptive)'
        }
        
        cvzone.putTextRect(img, f'Free: {space_counter}/{len(posList)}', 
                          (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))
        cvzone.putTextRect(img, f'Threshold: {current_threshold}', 
                          (100, 120), scale=1.5, thickness=2, offset=10, colorR=(102, 126, 234))
        cvzone.putTextRect(img, f'Mode: {detection_info.get(detection_type, "Multi-Lane")}', 
                          (100, 170), scale=1, thickness=2, offset=10, colorR=(102, 126, 234))
        
        return space_counter

    # Main video processing loop
    frame_count = 0
    while cap.isOpened():
        success, img = cap.read()
        if not success:
            break

        # Standard preprocessing pipeline
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
        img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY_INV, 25, 16)
        img_median = cv2.medianBlur(img_threshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(img_median, kernel, iterations=1)

        # Detect parking spaces
        check_parking_space(img_dilate, img, current_frame=img_gray)

        # MJPEG encoding
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\\r\\n'
               b'Content-Type: image/jpeg\\r\\n\\r\\n' + frame + b'\\r\\n')
        
        frame_counter += 1
        
        # Optional: Log progress every 100 frames
        if frame_counter % 100 == 0:
            print(f"[PROGRESS] Processed {frame_counter} frames, using threshold: {adaptive_detector.last_threshold}")
'''


# ═══════════════════════════════════════════════════════════════════
# OPTION B: MINIMAL CHANGES (if you want to keep more original code)
# ═══════════════════════════════════════════════════════════════════
"""
Add these lines at the START of generate_frames():

    # Initialize adaptive threshold detection
    from parkingapp.adaptive_detection import AdaptiveThresholdCalculator, AdaptiveDetector
    
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    calculator = AdaptiveThresholdCalculator(sample_frame_count=15)
    calibration = calculator.analyze_sample_frames(cap, posList)
    adaptive_threshold = AdaptiveDetector(base_threshold=calibration['optimal_threshold'])


And replace this line in check_parking_space():

    BEFORE:
    ───────
    if count < 900:

    AFTER:
    ──────
    if count < adaptive_threshold.last_threshold:
"""


# ═══════════════════════════════════════════════════════════════════
# TESTING: Quick test script
# ═══════════════════════════════════════════════════════════════════

TEST_CODE = '''
# Run this in Django shell to test calibration:
# python manage.py shell

import pickle
import os
from parkingapp.adaptive_detection import calibrate_video

# Load parking positions
pos_file = 'parkingapp/CarParkPos'
with open(pos_file, 'rb') as f:
    posList = pickle.load(f)

print(f"Loaded {len(posList)} parking spaces")

# Test with your video
video_path = 'media/parking_lot_video.mp4'
if os.path.exists(video_path):
    print(f"Calibrating for: {video_path}")
    result = calibrate_video(video_path, posList, sample_frames=30)
    
    print("\\n=== CALIBRATION RESULTS ===")
    for key, value in result.items():
        print(f"  {key}: {value}")
else:
    print(f"Video not found: {video_path}")
'''


# ═══════════════════════════════════════════════════════════════════
# STEP-BY-STEP INTEGRATION CHECKLIST
# ═══════════════════════════════════════════════════════════════════

INTEGRATION_CHECKLIST = """
✓ STEP 1: Verify adaptive_detection.py exists
  - File: parkingapp/adaptive_detection.py
  - Contains: AdaptiveThresholdCalculator, AdaptiveDetector, VideoResolutionAdapter

✓ STEP 2: Update detection_config.py
  - Added: ENABLE_ADAPTIVE_THRESHOLDS, ADAPTIVE_CALIBRATION_FRAMES
  - Status: Already done in this commit

✓ STEP 3: Add import in views.py (at top after existing imports)
  - Add: from parkingapp.adaptive_detection import AdaptiveThresholdCalculator, ...
  - Location: After other imports around line 20

✓ STEP 4: Replace generate_frames() function
  - Option A (recommended): Copy OPTION_A_CODE above
  - Option B (minimal): Add initialization + change threshold check

✓ STEP 5: Test with a video
  - Upload a video through Django admin
  - Visit /video page
  - Watch console output for "[CALIBRATION RESULTS]"
  - Compare accuracy with different resolutions/lighting

✓ STEP 6 (Optional): Also update generate_frames_yolov8()
  - Apply same adaptive threshold logic
  - See generate_frames_yolov8() starting at line 401 in views.py
"""


# ═══════════════════════════════════════════════════════════════════
# TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════════

TROUBLESHOOTING = """
Q: ImportError: cannot import name 'AdaptiveThresholdCalculator'
A: Make sure parkingapp/adaptive_detection.py exists

Q: Calibration takes too long
A: Reduce sample frames: AdaptiveThresholdCalculator(sample_frame_count=10)

Q: Threshold still seems wrong
A: Check console for [CALIBRATION RESULTS] - verify mean_empty < mean_occupied

Q: Video shows only red boxes (all occupied)
A: Threshold is too LOW - increase sample_frame_count or check video quality

Q: Video shows only green boxes (all empty)  
A: Threshold is too HIGH - verify parking spaces are marked correctly in posList

Q: Need to manually override threshold
A: Pass threshold as URL param: /video/?threshold=1400
"""
