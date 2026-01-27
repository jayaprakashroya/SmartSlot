#!/usr/bin/env python
"""
YOLOv8 Model Switcher - Easily switch between different YOLOv8 models
"""

import os
import re
import sys

DETECTOR_FILE = "parkingapp/yolov8_detector.py"

MODELS = {
    '1': ('yolov8n.pt', 'Nano - Fast (25-30 FPS), Less Accurate'),
    '2': ('yolov8s.pt', 'Small - Balanced (7-10 FPS), Good Accuracy - RECOMMENDED'),
    '3': ('yolov8m.pt', 'Medium - Slower (3-5 FPS), Better Accuracy'),
    '4': ('yolov8l.pt', 'Large - Slowest (1-2 FPS), Best Accuracy'),
}

def print_banner():
    print("\n" + "="*70)
    print("           YOLOv8 MODEL SWITCHER - Parking Detection")
    print("="*70)

def show_current_model():
    """Show currently configured model"""
    try:
        with open(DETECTOR_FILE, 'r') as f:
            content = f.read()
            match = re.search(r'model_name:\s*str\s*=\s*"(yolov8[nlms]\.pt)"', content)
            if match:
                current = match.group(1)
                print(f"\n📍 Currently Configured: {current}")
                return current
    except Exception as e:
        print(f"❌ Error reading current model: {e}")
    return None

def show_models():
    """Show available models"""
    print("\n📦 Available YOLOv8 Models:\n")
    for num, (model, desc) in MODELS.items():
        print(f"  {num}. {model:15} - {desc}")
    print()

def switch_model(model_name):
    """Switch to a different model"""
    try:
        with open(DETECTOR_FILE, 'r') as f:
            content = f.read()
        
        # Replace the default model
        new_content = re.sub(
            r'def __init__\(self, model_name: str = "yolov8[nlms]\.pt"',
            f'def __init__(self, model_name: str = "{model_name}"',
            content
        )
        
        with open(DETECTOR_FILE, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Successfully switched to {model_name}")
        print(f"📝 Changes saved to {DETECTOR_FILE}")
        print(f"\n💡 Tip: Model will be downloaded on first use (if not cached)")
        return True
        
    except Exception as e:
        print(f"❌ Error switching model: {e}")
        return False

def main():
    print_banner()
    current = show_current_model()
    show_models()
    
    choice = input("Enter your choice (1-4) or 'q' to quit: ").strip().lower()
    
    if choice == 'q':
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    if choice not in MODELS:
        print("❌ Invalid choice. Please enter 1, 2, 3, or 4")
        sys.exit(1)
    
    model_name, description = MODELS[choice]
    
    if current == model_name:
        print(f"\n✓ Already using {model_name}")
        sys.exit(0)
    
    print(f"\n🔄 Switching to: {model_name}")
    print(f"   {description}\n")
    
    if switch_model(model_name):
        print("\n🚀 Ready to use! Start your parking detection:")
        print("   python manage.py runserver")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
