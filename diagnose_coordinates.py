"""
Diagnostic to check if parking coordinates match video
"""
import pickle
import cv2
import os

print("=" * 70)
print("PARKING COORDINATES DIAGNOSTIC")
print("=" * 70)

# Load parking positions
pos_file = 'parkingapp/CarParkPos'
print(f"\n[1] Loading parking positions from: {pos_file}")

if not os.path.exists(pos_file):
    print(f"    ❌ File not found: {pos_file}")
    print("    Check if this is the correct path")
    exit(1)

try:
    with open(pos_file, 'rb') as f:
        posList = pickle.load(f)
    print(f"    ✅ Loaded {len(posList)} parking positions")
except Exception as e:
    print(f"    ❌ Error: {e}")
    exit(1)

# Show coordinates
print(f"\n[2] Parking spot coordinates (first 10):")
for i, (x, y) in enumerate(posList[:10]):
    print(f"    Spot {i+1}: x={x}, y={y}")

# Get coordinate ranges
if posList:
    x_coords = [x for x, y in posList]
    y_coords = [y for x, y in posList]
    print(f"\n[3] Coordinate ranges:")
    print(f"    X: {min(x_coords)} to {max(x_coords)}")
    print(f"    Y: {min(y_coords)} to {max(y_coords)}")

# Check if these coordinates make sense for a video
print(f"\n[4] Video dimensions check:")
print(f"    If your video is:")
print(f"    - 1280x720:  Coordinates look {'✅ OK' if max(x_coords) < 1280 and max(y_coords) < 720 else '❌ OUT OF RANGE'}")
print(f"    - 1920x1080: Coordinates look {'✅ OK' if max(x_coords) < 1920 and max(y_coords) < 1080 else '❌ OUT OF RANGE'}")
print(f"    - 640x480:   Coordinates look {'✅ OK' if max(x_coords) < 640 and max(y_coords) < 480 else '❌ OUT OF RANGE'}")

print(f"\n[5] Maximum coordinates:")
print(f"    Max X: {max(x_coords)}")
print(f"    Max Y: {max(y_coords)}")
print(f"    → Your video must be at least {max(x_coords)+120}x{max(y_coords)+60} pixels")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

if max(x_coords) > 1920 or max(y_coords) > 1080:
    print("❌ PROBLEM: Coordinates are too large!")
    print("   → Parking positions file is for a different/higher resolution video")
    print("   → Need to regenerate CarParkPos for your current video")
else:
    print("✅ Coordinates look reasonable")
    print("   → The issue might be with detection logic, not coordinates")
    print("   → Need to test detection with actual frame analysis")

print("\n" + "=" * 70)
