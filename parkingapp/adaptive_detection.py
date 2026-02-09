"""
Adaptive Parking Space Detection Module
=======================================

Solves the hardcoded threshold problem by automatically calibrating
detection parameters based on:
- Video resolution
- Lighting conditions (brightness histogram)
- Frame contrast
- Historical parking space occupancy patterns
"""

import cv2
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)


class AdaptiveThresholdCalculator:
    """
    Calculates optimal pixel count thresholds for different videos
    instead of using hardcoded values like 900.
    """
    
    def __init__(self, sample_frame_count=30):
        """
        Args:
            sample_frame_count: Number of frames to analyze for calibration
        """
        self.sample_frame_count = sample_frame_count
        self.pixel_counts = []
        self.brightness_values = []
        self.contrast_values = []
        self.frame_analysis = []
        
    def analyze_sample_frames(self, cap, posList, width=107, height=48):
        """
        Analyze first N frames to determine optimal thresholds.
        
        Args:
            cap: Video capture object
            posList: List of (x, y) coordinates for parking spaces
            width: Parking space width (default 107)
            height: Parking space height (default 48)
            
        Returns:
            dict with optimal thresholds for this video
        """
        frame_count = 0
        all_pixel_counts = []
        
        # Save original position in video
        original_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to start
        
        try:
            while frame_count < self.sample_frame_count:
                success, frame = cap.read()
                if not success:
                    break
                
                # Process frame through standard pipeline
                img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
                img_threshold = cv2.adaptiveThreshold(
                    img_blur, 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY_INV, 25, 16
                )
                img_median = cv2.medianBlur(img_threshold, 5)
                kernel = np.ones((3, 3), np.uint8)
                img_dilate = cv2.dilate(img_median, kernel, iterations=1)
                
                # Extract pixel counts from all spaces
                frame_pixels = []
                for pos in posList:
                    x, y = pos
                    img_crop = img_dilate[y:y + height, x:x + width]
                    count = cv2.countNonZero(img_crop)
                    frame_pixels.append(count)
                    all_pixel_counts.append(count)
                
                # Record frame metrics
                brightness = self._calculate_brightness(img_gray)
                contrast = self._calculate_contrast(img_gray)
                
                self.brightness_values.append(brightness)
                self.contrast_values.append(contrast)
                self.frame_analysis.append({
                    'frame': frame_count,
                    'pixel_counts': frame_pixels,
                    'brightness': brightness,
                    'contrast': contrast,
                    'avg_pixels': np.mean(frame_pixels)
                })
                
                frame_count += 1
        finally:
            # Restore original video position
            cap.set(cv2.CAP_PROP_POS_FRAMES, original_pos)
        
        # Calculate statistics
        all_pixel_counts = np.array(all_pixel_counts)
        thresholds = self._calculate_optimal_thresholds(all_pixel_counts)
        
        return {
            'optimal_threshold': thresholds['optimal'],
            'low_threshold': thresholds['low'],        # For bright/clear conditions
            'high_threshold': thresholds['high'],      # For dark/shadowy conditions
            'mean_occupied': thresholds['mean_occupied'],
            'mean_empty': thresholds['mean_empty'],
            'brightness_avg': np.mean(self.brightness_values),
            'contrast_avg': np.mean(self.contrast_values),
            'std_dev': np.std(all_pixel_counts),
            'samples_analyzed': frame_count * len(posList),
        }
    
    def _calculate_brightness(self, gray_img):
        """Calculate average brightness of image"""
        return np.mean(gray_img)
    
    def _calculate_contrast(self, gray_img):
        """Calculate contrast (standard deviation of pixel values)"""
        return np.std(gray_img)
    
    def _calculate_optimal_thresholds(self, pixel_counts):
        """
        Calculate optimal threshold using improved statistical analysis.
        
        Handles cases where:
        - Parking lot has mixed lighting (shadows, reflections)
        - Spots have varying sizes and angles
        - Need robust bimodal distribution split
        """
        sorted_counts = np.sort(pixel_counts)
        
        # Use percentile-based approach for robustness
        p10 = np.percentile(sorted_counts, 10)   # Very likely empty
        p25 = np.percentile(sorted_counts, 25)
        p50 = np.percentile(sorted_counts, 50)   # Median
        p75 = np.percentile(sorted_counts, 75)
        p90 = np.percentile(sorted_counts, 90)   # Very likely occupied
        
        # Better separation: use inner quartiles for cleaner split
        empty_counts = sorted_counts[sorted_counts <= p25]
        occupied_counts = sorted_counts[sorted_counts >= p75]
        middle_counts = sorted_counts[(sorted_counts > p25) & (sorted_counts < p75)]
        
        # Calculate means from confident groups
        mean_empty = np.mean(empty_counts) if len(empty_counts) > 5 else p10
        mean_occupied = np.mean(occupied_counts) if len(occupied_counts) > 5 else p90
        
        # Optimal threshold with safety margin (slightly toward empty)
        optimal = (mean_empty + mean_occupied) / 2
        optimal = int(optimal * 1.05)  # Bias toward detecting occupied (fewer false empty)
        
        # Conservative thresholds
        low = int(mean_empty + (optimal - mean_empty) * 0.6)    # More sensitive for empty
        high = int(mean_occupied - (mean_occupied - optimal) * 0.6)  # More sensitive for occupied
        
        return {
            'optimal': optimal,
            'low': low,
            'high': high,
            'mean_empty': int(mean_empty),
            'mean_occupied': int(mean_occupied),
            'p10': int(p10),
            'p90': int(p90),
            'middle_variance': float(np.std(middle_counts)) if len(middle_counts) > 0 else 0,
        }


class AdaptiveDetector:
    """
    Dynamically adjusts detection parameters based on frame characteristics
    """
    
    def __init__(self, base_threshold=1200):
        """
        Args:
            base_threshold: Starting threshold value (will be adjusted)
        """
        self.base_threshold = base_threshold
        self.brightness_history = deque(maxlen=30)
        self.threshold_history = deque(maxlen=30)
        self.last_threshold = base_threshold
        
    def get_adaptive_threshold(self, frame):
        """
        Calculate threshold for current frame based on its brightness.
        More conservative to avoid false positives/negatives.
        
        Args:
            frame: Processed binary frame (after dilation)
            
        Returns:
            int: Adjusted threshold for this frame
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        brightness = np.mean(gray)
        
        self.brightness_history.append(brightness)
        
        # More conservative brightness adjustment (±15% instead of ±30%)
        brightness_factor = 1.0 + (brightness - 127) / 127 * 0.15
        brightness_factor = np.clip(brightness_factor, 0.85, 1.15)  # Tighter range
        
        # Apply adjustment
        adaptive_threshold = int(self.base_threshold * brightness_factor)
        
        # Smooth changes to avoid jitter (moving average with higher weight on recent)
        self.threshold_history.append(adaptive_threshold)
        
        # Use weighted average: recent frames have more weight
        history_list = list(self.threshold_history)
        weights = np.linspace(0.5, 1.5, len(history_list))
        smoothed_threshold = int(np.average(history_list, weights=weights))
        
        self.last_threshold = smoothed_threshold
        return smoothed_threshold
        
        self.last_threshold = smoothed_threshold
        return smoothed_threshold
    
    def should_recalibrate(self, frame, interval=100):
        """
        Determine if thresholds should be recalibrated
        (detects significant environmental changes)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        brightness = np.mean(gray)
        
        if len(self.brightness_history) < interval:
            return False
        
        # Check if brightness changed significantly
        past_avg = np.mean(list(self.brightness_history)[:interval//2])
        recent_avg = np.mean(list(self.brightness_history)[-interval//2:])
        
        brightness_change = abs(recent_avg - past_avg)
        return brightness_change > 30  # Threshold for recalibration


class VideoResolutionAdapter:
    """
    Adjusts detection parameters based on video resolution
    """
    
    # Empirically determined threshold ratios for different resolutions
    RESOLUTION_THRESHOLDS = {
        (640, 360): 0.6,      # Small resolution: lower threshold
        (1280, 720): 1.0,     # Standard HD: baseline
        (1920, 1080): 1.4,    # Full HD: higher threshold
        (2560, 1440): 1.8,    # 2K: higher
        (3840, 2160): 2.5,    # 4K: much higher
    }
    
    PARKING_SPACE_PIXELS = {
        (640, 360): 30 * 16,    # ~480 pixels
        (1280, 720): 107 * 48,  # ~5136 pixels (standard)
        (1920, 1080): 160 * 72, # ~11520 pixels
    }
    
    @classmethod
    def get_threshold_for_resolution(cls, resolution, base_threshold=1200):
        """
        Scale threshold based on video resolution.
        
        Args:
            resolution: Tuple of (width, height)
            base_threshold: Standard threshold (for 1280x720)
            
        Returns:
            int: Adjusted threshold for this resolution
        """
        # Find closest resolution
        closest_res = min(
            cls.RESOLUTION_THRESHOLDS.keys(),
            key=lambda r: abs(r[0] - resolution[0]) + abs(r[1] - resolution[1])
        )
        
        ratio = cls.RESOLUTION_THRESHOLDS[closest_res]
        adjusted = int(base_threshold * ratio)
        
        logger.info(
            f"Resolution {resolution} -> closest {closest_res} "
            f"-> threshold {base_threshold} * {ratio} = {adjusted}"
        )
        
        return adjusted
    
    @classmethod
    def get_parking_space_size(cls, resolution):
        """
        Get optimal parking space crop size for resolution.
        
        Returns:
            Tuple of (width, height)
        """
        if resolution in cls.PARKING_SPACE_PIXELS:
            total_pixels = cls.PARKING_SPACE_PIXELS[resolution]
        else:
            # Scale from 1280x720 baseline
            scale = (resolution[0] / 1280) * (resolution[1] / 720)
            total_pixels = int(107 * 48 * scale)
        
        # Assuming 2.2:1 aspect ratio (typical parking space)
        width = int(np.sqrt(total_pixels * 2.2))
        height = int(width / 2.2)
        
        return (width, height)


# Example usage functions
def calibrate_video(video_path, posList, sample_frames=30):
    """
    Calibrate optimal thresholds for a specific video.
    
    Args:
        video_path: Path to video file
        posList: List of parking space coordinates
        sample_frames: Number of frames to analyze
        
    Returns:
        dict: Calibration results with optimal thresholds
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return None
    
    try:
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(
            f"Video: {width}x{height} @ {fps}fps, {total_frames} frames"
        )
        
        # Calibrate thresholds
        calculator = AdaptiveThresholdCalculator(sample_frame_count=sample_frames)
        thresholds = calculator.analyze_sample_frames(cap, posList)
        
        # Adjust for resolution
        thresholds['resolution_adjusted'] = VideoResolutionAdapter.get_threshold_for_resolution(
            (width, height)
        )
        
        logger.info(f"Calibration results: {thresholds}")
        return thresholds
        
    finally:
        cap.release()


def get_dynamic_threshold_for_video(video_path, posList):
    """
    One-line function to get optimal threshold for a video.
    Use this in your Django views to auto-calibrate.
    
    Example:
        threshold = get_dynamic_threshold_for_video('parking_lot.mp4', posList)
        # Use threshold in detection instead of hardcoded 900
    """
    result = calibrate_video(video_path, posList, sample_frames=20)
    if result:
        return result['optimal_threshold']
    return 1200  # Fallback
