"""
Detection Configuration - Easily adjustable thresholds
for parking spot accuracy without modifying view code
"""

# ═══════════════════════════════════════════════════════════════════
# YOLO CONFIDENCE THRESHOLDS (for YOLOv8 vehicle detection)
# ═══════════════════════════════════════════════════════════════════

# Initial detection threshold - filters out very low confidence predictions
YOLO_DETECTION_THRESHOLD = 0.75  # 75% - High confidence to reduce false positives
# Increase to 0.85-0.95 if still getting false positives
# Decrease to 0.50-0.65 if missing real vehicles

# Assignment threshold - vehicles must be this confident to auto-assign to spots
YOLO_ASSIGNMENT_THRESHOLD = 0.90  # 90% - Very strict for database recording
# Increase to 0.95 for maximum strictness
# Decrease to 0.85 for more assignments

# ═══════════════════════════════════════════════════════════════════
# SPOT OVERLAP THRESHOLDS (for matching vehicle detection to spot location)
# ═══════════════════════════════════════════════════════════════════

# Minimum overlap (IoU) for a vehicle to be assigned to a spot
SPOT_OVERLAP_THRESHOLD = 0.25  # 25% - Vehicle must overlap at least 25% of spot area
# Increase to 0.30-0.40 for stricter matching
# Decrease to 0.15-0.20 for more lenient matching

# ═══════════════════════════════════════════════════════════════════
# PIXEL-COUNTING THRESHOLDS (for legacy detection without YOLOv8)
# ═══════════════════════════════════════════════════════════════════
# These are non-zero pixel counts in a spot region
# Higher = stricter (fewer false occupied detections)

PIXEL_COUNT_THRESHOLDS = {
    'multi_lane': 1200,      # Default detection mode
    'reserved_spot': 1100,   # Reserved spots - more sensitive
    'night_vision': 1300,    # Night mode - less sensitive (more light artifacts)
    'angled_spot': 1150,     # Angled spots - moderate sensitivity
}

# Individual threshold overrides (optional)
# PIXEL_COUNT_THRESHOLDS['multi_lane'] = 1400  # Make it stricter

# ═══════════════════════════════════════════════════════════════════
# DOUBLE PARKING DETECTION THRESHOLD
# ═══════════════════════════════════════════════════════════════════

# Intersection over Union (IoU) for detecting overlapping vehicles
DOUBLE_PARKING_IoU_THRESHOLD = 0.60  # 60% overlap = flag as double parked
# Increase to 0.70-0.80 for stricter double parking detection
# Decrease to 0.50 for more sensitive detection

# ═══════════════════════════════════════════════════════════════════
# QUICK ADJUSTMENT GUIDE
# ═══════════════════════════════════════════════════════════════════
"""
PROBLEM: Too many empty spots marked as OCCUPIED (Red)
SOLUTION: 
  1. Increase PIXEL_COUNT_THRESHOLDS (e.g., multi_lane: 1200 -> 1400)
  2. Increase YOLO_DETECTION_THRESHOLD (e.g., 0.75 -> 0.85)
  3. Increase SPOT_OVERLAP_THRESHOLD (e.g., 0.25 -> 0.35)

PROBLEM: Can't find parked vehicles (False negatives)
SOLUTION:
  1. Decrease PIXEL_COUNT_THRESHOLDS (e.g., multi_lane: 1200 -> 1000)
  2. Decrease YOLO_DETECTION_THRESHOLD (e.g., 0.75 -> 0.60)
  3. Decrease SPOT_OVERLAP_THRESHOLD (e.g., 0.25 -> 0.15)

PROBLEM: Shadows being detected as vehicles
SOLUTION:
  1. Increase all thresholds significantly
  2. Increase YOLO_DETECTION_THRESHOLD to 0.85+
  3. Use time-based filtering to require sustained detection

PROBLEM: Motorcycles/small vehicles not detected
SOLUTION:
  1. Decrease SPOT_OVERLAP_THRESHOLD slightly (to 0.20)
  2. Use separate YOLO model trained on motorcycles
"""

def get_pixel_threshold(detection_type='multi_lane'):
    """Get pixel count threshold for detection type"""
    return PIXEL_COUNT_THRESHOLDS.get(detection_type, PIXEL_COUNT_THRESHOLDS['multi_lane'])


def adjust_thresholds_for_daytime():
    """Adjust thresholds for daytime (better lighting)"""
    return {
        'yolo_detection': 0.80,
        'pixel_count_multi_lane': 1300,
        'yolo_assignment': 0.92
    }


def adjust_thresholds_for_nighttime():
    """Adjust thresholds for nighttime (worse lighting)"""
    return {
        'yolo_detection': 0.65,
        'pixel_count_multi_lane': 900,
        'yolo_assignment': 0.85
    }


def adjust_thresholds_for_rain_weather():
    """Adjust thresholds for rainy weather (reflections, artifacts)"""
    return {
        'yolo_detection': 0.72,
        'pixel_count_multi_lane': 1400,  # More strict
        'yolo_assignment': 0.91
    }


# ═══════════════════════════════════════════════════════════════════
# DYNAMIC/ADAPTIVE THRESHOLD CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
"""
Instead of hardcoded thresholds, use adaptive detection that automatically
calibrates for each video based on:
- Video resolution
- Lighting conditions
- Frame contrast
- Historical patterns

See adaptive_detection.py for implementation.
"""

ENABLE_ADAPTIVE_THRESHOLDS = True  # Enable auto-calibration
ADAPTIVE_CALIBRATION_FRAMES = 30   # Sample N frames for calibration
ADAPTIVE_SMOOTHING_WINDOW = 10     # Smooth threshold changes over N frames

# Brightness change threshold for auto-recalibration (0-255 scale)
BRIGHTNESS_CHANGE_THRESHOLD = 30   # Recalibrate if brightness changes by this much

# Use adaptive detection or fall back to config-based thresholds
USE_ADAPTIVE_MODE = True  # False = use static PIXEL_COUNT_THRESHOLDS above
