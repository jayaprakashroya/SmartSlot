"""
Debug script to test YOLO detection in real video
"""
import cv2
from parkingapp.yolov8_detection import ParkingSpaceDetector

print("=" * 70)
print("YOLO DEBUG - Testing Vehicle Detection")
print("=" * 70)

# Test with a video file
print("\n[1] Loading detector...")
try:
    detector = ParkingSpaceDetector(model_name='yolov8n.pt')
    print("    ✅ Detector loaded")
except Exception as e:
    print(f"    ❌ Error: {e}")
    exit(1)

# Test frames from video
print("\n[2] Testing with sample parking spaces...")

# Create a test frame (gray parking lot)
test_frame = cv2.imread('sample_parking_frame.jpg')  # Change path if needed
if test_frame is None:
    print("    ⚠️  No test image found, creating synthetic frame...")
    import numpy as np
    test_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 100

print(f"    Frame size: {test_frame.shape}")

# Test detection with different thresholds
print("\n[3] Testing detection with various thresholds:")
for model_conf in [0.05, 0.1, 0.25, 0.5]:
    # Manually set model confidence by re-running
    results = detector.model(test_frame, conf=model_conf, verbose=False)
    count = 0
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            if cls_id in detector.vehicle_classes:
                count += 1
    print(f"    Model conf={model_conf}: {count} vehicles detected")

print("\n[4] Checking parking spot detection logic:")

# Create test parking positions
test_positions = [
    (100, 100), (210, 100), (320, 100),
    (100, 160), (210, 160), (320, 160),
]

# Test with empty frame
detections_empty = detector.detect_vehicles(test_frame, conf_threshold=0.15)
results_empty = detector.analyze_parking_space(test_frame, test_positions, detections_empty)

print(f"    Empty frame:")
print(f"      Detections: {len(detections_empty)}")
print(f"      Available: {results_empty['statistics']['available_count']}")
print(f"      Occupied: {results_empty['statistics']['occupied_count']}")
print(f"      Expected: All available (no vehicles)")

# Draw a fake vehicle in one spot
import cv2
test_frame_with_car = test_frame.copy()
cv2.rectangle(test_frame_with_car, (95, 95), (215, 155), (200, 0, 0), -1)  # Blue rectangle

detections_with_car = detector.detect_vehicles(test_frame_with_car, conf_threshold=0.15)
results_with_car = detector.analyze_parking_space(test_frame_with_car, test_positions, detections_with_car)

print(f"\n    With simulated vehicle:")
print(f"      Detections: {len(detections_with_car)}")
print(f"      Available: {results_with_car['statistics']['available_count']}")
print(f"      Occupied: {results_with_car['statistics']['occupied_count']}")
print(f"      Expected: 1 occupied, 5 available")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)

# Key question
print("\nKEY ISSUE:")
if len(detections_empty) > 0 and len(detections_with_car) == 0:
    print("❌ YOLOv8 only detects random noise, not vehicles")
    print("   Fix: Model not working correctly, try different model or retrain")
elif len(detections_with_car) > 0 and results_with_car['statistics']['occupied_count'] == 0:
    print("❌ Vehicles detected but not marking spots as occupied")
    print("   Fix: Overlap calculation or coordinates are wrong")
else:
    print("⚠️  Check output above to diagnose the issue")
