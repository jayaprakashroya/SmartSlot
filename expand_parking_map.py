"""
Expand and regenerate the parking spot map to cover the entire visible parking lot
This script intelligently extends the existing spot list to cover all areas
"""

import pickle
import numpy as np
from pathlib import Path

def expand_parking_spots_to_full_lot(input_file='parkingapp/CarParkPos', 
                                      output_file='parkingapp/CarParkPos_Full',
                                      frame_width=1280, frame_height=720):
    """
    Expand existing parking spots to cover the entire parking lot.
    Analyzes the current spot distribution and extends it.
    
    Args:
        input_file: Current parking positions file
        output_file: Output file with expanded positions
        frame_width: Video frame width
        frame_height: Video frame height
    """
    
    try:
        with open(input_file, 'rb') as f:
            current_spots = pickle.load(f)
        print(f"✓ Loaded {len(current_spots)} existing spots")
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_file}")
        return False
    
    # Analyze current spot distribution
    current_spots = np.array(current_spots)
    
    # Get bounding box of current spots
    min_x = current_spots[:, 0].min()
    max_x = current_spots[:, 0].max()
    min_y = current_spots[:, 1].min()
    max_y = current_spots[:, 1].max()
    
    print(f"\nCurrent spot coverage:")
    print(f"  X: {min_x} to {max_x} (width: {max_x - min_x})")
    print(f"  Y: {min_y} to {max_y} (height: {max_y - min_y})")
    print(f"  Frame size: {frame_width}x{frame_height}")
    
    # Calculate average spacing between spots
    unique_rows = {}
    for x, y in current_spots:
        if y not in unique_rows:
            unique_rows[y] = []
        unique_rows[y].append(x)
    
    # Find patterns
    row_spacings = []
    col_spacings = []
    
    for y, x_coords in unique_rows.items():
        x_coords = sorted(x_coords)
        for i in range(len(x_coords) - 1):
            col_spacings.append(x_coords[i+1] - x_coords[i])
    
    for y_coords in sorted(unique_rows.keys()):
        pass
    
    # Get average spacing (with margin for variation)
    avg_col_spacing = np.mean(col_spacings) if col_spacings else 115
    avg_row_spacing = 60  # Approximate row height
    
    print(f"\nAverage spacing:")
    print(f"  Column spacing: {avg_col_spacing:.1f} pixels")
    print(f"  Row spacing: {avg_row_spacing} pixels")
    
    # Generate extended spot list
    expanded_spots = [(int(x), int(y)) for x, y in current_spots]
    spot_width, spot_height = 107, 48
    
    # Extend left
    if min_x > 50:
        print("\n🔄 Extending spots to the LEFT...")
        x = min_x - avg_col_spacing
        while x >= 0:
            for y in unique_rows.keys():
                if x >= 0 and x + spot_width <= frame_width and y >= 0 and y + spot_height <= frame_height:
                    expanded_spots.append((int(x), int(y)))
            x -= avg_col_spacing
    
    # Extend right
    if max_x + spot_width < frame_width - 50:
        print("🔄 Extending spots to the RIGHT...")
        x = max_x + avg_col_spacing
        while x + spot_width <= frame_width:
            for y in unique_rows.keys():
                if x >= 0 and x + spot_width <= frame_width and y >= 0 and y + spot_height <= frame_height:
                    expanded_spots.append((int(x), int(y)))
            x += avg_col_spacing
    
    # Extend top
    if min_y > 50:
        print("🔄 Extending spots UPWARD...")
        y = min_y - avg_row_spacing
        while y >= 0:
            for x in sorted(set([int(p[0]) for p in expanded_spots if int(p[1]) == min_y])):
                if x >= 0 and x + spot_width <= frame_width and y >= 0 and y + spot_height <= frame_height:
                    expanded_spots.append((x, int(y)))
            y -= avg_row_spacing
    
    # Extend bottom
    if max_y + spot_height < frame_height - 50:
        print("🔄 Extending spots DOWNWARD...")
        y = max_y + avg_row_spacing
        while y + spot_height <= frame_height:
            for x in sorted(set([int(p[0]) for p in expanded_spots if int(p[1]) == max_y])):
                if x >= 0 and x + spot_width <= frame_width and y >= 0 and y + spot_height <= frame_height:
                    expanded_spots.append((x, int(y)))
            y += avg_row_spacing
    
    # Remove duplicates
    expanded_spots = list({spot for spot in expanded_spots})
    expanded_spots.sort()
    
    print(f"\n✅ Generated {len(expanded_spots)} total parking spots")
    print(f"   (Expanded from {len(current_spots)} to {len(expanded_spots)} spots)")
    
    # Save expanded spots
    try:
        Path('parkingapp').mkdir(exist_ok=True)
        with open(output_file, 'wb') as f:
            pickle.dump(expanded_spots, f)
        print(f"\n✅ Saved expanded spots to {output_file}")
        
        # Also backup and replace the original
        print(f"🔄 Backing up original CarParkPos...")
        with open(input_file + '.backup', 'wb') as f:
            pickle.dump(current_spots, f)
        
        print(f"🔄 Replacing original CarParkPos with expanded version...")
        with open(input_file, 'wb') as f:
            pickle.dump(expanded_spots, f)
        
        print(f"✅ Updated CarParkPos with {len(expanded_spots)} spots")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


def create_dense_parking_grid(rows=20, cols=8, output_file='parkingapp/CarParkPos'):
    """
    Create a complete grid of parking spots covering the entire lot.
    More spots than typical, to ensure full coverage.
    
    Args:
        rows: Number of spot rows
        cols: Number of spot columns
        output_file: Output file path
    """
    spot_width, spot_height = 107, 48
    spacing_x = 120  # Horizontal spacing
    spacing_y = 65   # Vertical spacing
    
    parking_spots = []
    start_x, start_y = 40, 80
    
    print(f"🔄 Creating dense grid: {rows}x{cols} = {rows*cols} spots")
    
    for row in range(rows):
        for col in range(cols):
            x = start_x + (col * spacing_x)
            y = start_y + (row * spacing_y)
            
            # Only add if within video bounds (1280x720)
            if x >= 0 and y >= 0 and (x + spot_width) <= 1280 and (y + spot_height) <= 720:
                parking_spots.append((x, y))
    
    print(f"✓ Generated {len(parking_spots)} valid grid spots")
    
    # Save to pickle file
    try:
        Path('parkingapp').mkdir(exist_ok=True)
        with open(output_file, 'wb') as f:
            pickle.dump(parking_spots, f)
        print(f"✅ Saved {len(parking_spots)} spots to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    import os
    
    print("=" * 70)
    print("FULL PARKING LOT EXPANSION TOOL")
    print("=" * 70)
    
    # Step 1: Try to expand existing spots
    if os.path.exists('parkingapp/CarParkPos'):
        print("\n📍 Found existing CarParkPos file")
        print("Attempting to expand to full lot coverage...\n")
        
        success = expand_parking_spots_to_full_lot()
        
        if success:
            print("\n✅ Successfully expanded parking spot map!")
            print("\nTo verify, run: python -c \"import pickle; pos = pickle.load(open('parkingapp/CarParkPos', 'rb')); print(f'Total spots: {len(pos)}')\"")
        else:
            print("\n⚠️  Expansion failed, creating dense grid instead...")
            create_dense_parking_grid()
    else:
        print("\n⚠️  CarParkPos file not found")
        print("Creating complete dense grid of parking spots...\n")
        create_dense_parking_grid()
    
    print("\n" + "=" * 70)
    print("✅ Parking spot mapping complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Restart the Django server: python manage.py runserver")
    print("2. Visit the video page to see full parking lot detection")
    print("=" * 70)
