"""
Generate a complete parking spot map for the entire parking lot
This script analyzes a video frame to detect all parking spots automatically
"""

import cv2
import pickle
import numpy as np
from pathlib import Path

def generate_parking_spots_from_frame(frame_path, output_file='parkingapp/CarParkPos'):
    """
    Generate parking spots by analyzing a parking lot image/frame.
    Uses contour detection to find all spot boundaries.
    
    Args:
        frame_path: Path to parking lot image/frame
        output_file: Output pickle file for spot positions
    """
    
    # Load the frame
    frame = cv2.imread(frame_path)
    if frame is None:
        print(f"❌ Error: Cannot load image from {frame_path}")
        return False
    
    print(f"✓ Loaded frame: {frame.shape}")
    height, width = frame.shape[:2]
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply morphological operations to find parking lines
    # First, apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Find edges to detect parking spot boundaries
    edges = cv2.Canny(enhanced, 30, 100)
    
    # Dilate to connect nearby edges (parking spot lines)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # Find contours (parking spots)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    parking_spots = []
    spot_width, spot_height = 107, 48
    
    print(f"Found {len(contours)} potential spot regions")
    
    # Filter and process contours to find valid parking spots
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter by approximate parking spot size
        # Parking spots should be roughly 107x48 pixels
        if (80 < w < 150) and (35 < h < 70):
            # Check if spot is within frame bounds
            if x >= 0 and y >= 0 and (x + spot_width) <= width and (y + spot_height) <= height:
                parking_spots.append((x, y))
    
    print(f"✓ Detected {len(parking_spots)} valid parking spots")
    
    # Sort spots by position (top to bottom, left to right)
    parking_spots.sort(key=lambda p: (p[1], p[0]))
    
    # Save to pickle file
    try:
        Path('parkingapp').mkdir(exist_ok=True)
        with open(output_file, 'wb') as f:
            pickle.dump(parking_spots, f)
        print(f"✅ Saved {len(parking_spots)} parking spots to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


def extract_frame_from_video(video_path, frame_number=0, output_frame='parking_sample.jpg'):
    """
    Extract a frame from video to use for parking spot generation.
    
    Args:
        video_path: Path to video file
        frame_number: Which frame to extract (default: 0 = first frame)
        output_frame: Where to save the frame
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Cannot open video: {video_path}")
        return None
    
    # Set frame position
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    success, frame = cap.read()
    cap.release()
    
    if not success:
        print(f"❌ Cannot extract frame {frame_number}")
        return None
    
    # Save frame
    cv2.imwrite(output_frame, frame)
    print(f"✓ Extracted frame to {output_frame}")
    return output_frame


def create_grid_parking_map(num_rows=15, num_cols=6, output_file='parkingapp/CarParkPos'):
    """
    Create a simple grid-based parking spot map.
    Useful if automatic detection fails.
    
    Args:
        num_rows: Number of rows of parking spots
        num_cols: Number of columns of parking spots
        output_file: Output pickle file
    """
    spot_width, spot_height = 107, 48
    spacing_x, spacing_y = 115, 60  # Space between spot centers
    
    parking_spots = []
    start_x, start_y = 50, 90
    
    for row in range(num_rows):
        for col in range(num_cols):
            x = start_x + (col * spacing_x)
            y = start_y + (row * spacing_y)
            
            # Only add if within video bounds (1280x720)
            if x < 1280 - spot_width and y < 720 - spot_height:
                parking_spots.append((x, y))
    
    print(f"✓ Generated {len(parking_spots)} grid-based parking spots")
    
    # Save to pickle file
    try:
        Path('parkingapp').mkdir(exist_ok=True)
        with open(output_file, 'wb') as f:
            pickle.dump(parking_spots, f)
        print(f"✅ Saved {len(parking_spots)} parking spots to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


def visualize_parking_spots(image_path, spots_file='parkingapp/CarParkPos', output_image='parking_with_spots.jpg'):
    """
    Visualize parking spots on the image.
    
    Args:
        image_path: Path to parking lot image
        spots_file: Path to parking spots pickle file
        output_image: Output image with visualized spots
    """
    # Load image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"❌ Cannot load image: {image_path}")
        return
    
    # Load parking spots
    try:
        with open(spots_file, 'rb') as f:
            spots = pickle.load(f)
        print(f"✓ Loaded {len(spots)} spots from {spots_file}")
    except FileNotFoundError:
        print(f"❌ Spots file not found: {spots_file}")
        return
    
    # Draw spots
    spot_width, spot_height = 107, 48
    for i, (x, y) in enumerate(spots):
        cv2.rectangle(frame, (x, y), (x + spot_width, y + spot_height), (0, 255, 0), 2)
        cv2.putText(frame, str(i+1), (x + 5, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Save visualization
    cv2.imwrite(output_image, frame)
    print(f"✅ Saved visualization to {output_image}")


if __name__ == '__main__':
    import os
    
    print("=" * 60)
    print("FULL PARKING LOT MAPPING GENERATOR")
    print("=" * 60)
    
    # Option 1: Try to generate from an image if available
    sample_images = [
        'parking_sample.jpg',
        'assets/parking_sample.jpg',
        'test_frame.jpg'
    ]
    
    generated = False
    for img_path in sample_images:
        if os.path.exists(img_path):
            print(f"\n📸 Found image: {img_path}")
            print("Generating parking spots from image...")
            generated = generate_parking_spots_from_frame(img_path)
            if generated:
                break
    
    # Option 2: If no image found, create grid-based map
    if not generated:
        print("\n⚠️  No image found for automatic detection")
        print("Creating grid-based parking spot map...")
        print("\nFor best results, provide a parking lot image and run:")
        print("  generate_parking_spots_from_frame('path/to/parking_image.jpg')")
        print("\nOr upload a clear image of your parking lot...")
        
        # Create grid map as fallback
        create_grid_parking_map(num_rows=15, num_cols=6)
    
    # Visualize if spots file exists
    if os.path.exists('parkingapp/CarParkPos'):
        print("\n🎨 Creating visualization...")
        if os.path.exists('parking_sample.jpg'):
            visualize_parking_spots('parking_sample.jpg')
    
    print("\n" + "=" * 60)
    print("✅ Parking spot map generation complete!")
    print("=" * 60)
