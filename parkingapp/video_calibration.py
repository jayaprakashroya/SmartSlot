"""
Video calibration module for multi-video support
Automatically detects video resolution and scales parking spot dimensions
"""

import cv2
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VideoCalibrator:
    """Handle video resolution detection and calibration"""
    
    # Base resolution used for original parking spot dimensions
    BASE_RESOLUTION_WIDTH = 1280
    BASE_RESOLUTION_HEIGHT = 720
    
    # Original hardcoded dimensions (calibrated for base resolution)
    BASE_SPACE_WIDTH = 107
    BASE_SPACE_HEIGHT = 48
    
    @classmethod
    def get_scaled_dimensions(cls, frame) -> Tuple[int, int]:
        """
        Get parking spot dimensions scaled to frame resolution
        
        Automatically scales the parking spot dimensions from the original
        base resolution (1280×720) to the current video resolution.
        
        Args:
            frame: Video frame (numpy array) or None
            
        Returns:
            Tuple of (space_width, space_height) scaled to frame resolution
            
        Example:
            >>> frame = cv2.imread('parking.jpg')  # 1920×1080
            >>> width, height = VideoCalibrator.get_scaled_dimensions(frame)
            >>> # Returns approximately (161, 72) - scaled 1.5x from base
        """
        if frame is None:
            logger.warning("Frame is None, returning base dimensions")
            return cls.BASE_SPACE_WIDTH, cls.BASE_SPACE_HEIGHT
        
        video_height, video_width = frame.shape[:2]
        
        # Calculate scaling factor based on width (primary dimension)
        width_scale = video_width / cls.BASE_RESOLUTION_WIDTH
        
        # Scale the dimensions proportionally
        # Minimum 50px width, 30px height to ensure visible rectangles
        scaled_width = max(50, int(cls.BASE_SPACE_WIDTH * width_scale))
        scaled_height = max(30, int(cls.BASE_SPACE_HEIGHT * width_scale))
        
        logger.info(f"Video resolution: {video_width}×{video_height}")
        logger.info(f"Scaling factor: {width_scale:.2f}x")
        logger.info(f"Scaled parking spot dimensions: {scaled_width}×{scaled_height} "
                   f"(base: {cls.BASE_SPACE_WIDTH}×{cls.BASE_SPACE_HEIGHT})")
        
        return scaled_width, scaled_height
    
    @classmethod
    def get_video_metadata(cls, video_path: str) -> Optional[Dict]:
        """
        Extract video metadata
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video properties or None if cannot open video
            
        Returns dict keys:
            - width: Video frame width in pixels
            - height: Video frame height in pixels
            - fps: Frames per second
            - total_frames: Total number of frames
            - duration_seconds: Total duration in seconds
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return None
        
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            duration_seconds = int(total_frames / fps) if fps > 0 else 0
            
            metadata = {
                'width': width,
                'height': height,
                'fps': fps,
                'total_frames': total_frames,
                'duration_seconds': duration_seconds
            }
            
            logger.info(f"Video metadata: {width}×{height} @ {fps:.1f}fps, "
                       f"{total_frames} frames ({duration_seconds}s)")
            
            return metadata
        finally:
            cap.release()
    
    @classmethod
    def get_scaling_factor(cls, video_width: int) -> float:
        """
        Calculate scaling factor for given video width
        
        Args:
            video_width: Video frame width in pixels
            
        Returns:
            Scaling factor (1.0 = base resolution, 2.0 = double size, etc)
        """
        return video_width / cls.BASE_RESOLUTION_WIDTH
    
    @classmethod
    def get_base_dimensions(cls) -> Tuple[int, int]:
        """
        Get the base parking spot dimensions used as reference
        
        Returns:
            Tuple of (base_width, base_height)
        """
        return cls.BASE_SPACE_WIDTH, cls.BASE_SPACE_HEIGHT
    
    @classmethod
    def get_base_resolution(cls) -> Tuple[int, int]:
        """
        Get the base video resolution used for calibration
        
        Returns:
            Tuple of (base_width, base_height)
        """
        return cls.BASE_RESOLUTION_WIDTH, cls.BASE_RESOLUTION_HEIGHT


class VideoMetadata:
    """Store and access video metadata"""
    
    def __init__(self, video_path: str):
        """
        Initialize with video path and extract metadata
        
        Args:
            video_path: Path to video file
        """
        self.video_path = video_path
        self.metadata = VideoCalibrator.get_video_metadata(video_path)
    
    def is_valid(self) -> bool:
        """Check if video metadata was successfully extracted"""
        return self.metadata is not None
    
    def get_width(self) -> int:
        """Get video width"""
        return self.metadata['width'] if self.is_valid() else 0
    
    def get_height(self) -> int:
        """Get video height"""
        return self.metadata['height'] if self.is_valid() else 0
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get video resolution as (width, height)"""
        return (self.get_width(), self.get_height())
    
    def get_fps(self) -> float:
        """Get frames per second"""
        return self.metadata['fps'] if self.is_valid() else 0
    
    def get_total_frames(self) -> int:
        """Get total frame count"""
        return self.metadata['total_frames'] if self.is_valid() else 0
    
    def get_duration_seconds(self) -> int:
        """Get video duration in seconds"""
        return self.metadata['duration_seconds'] if self.is_valid() else 0
    
    def __str__(self) -> str:
        if not self.is_valid():
            return f"VideoMetadata(invalid: {self.video_path})"
        
        w = self.get_width()
        h = self.get_height()
        fps = self.get_fps()
        duration = self.get_duration_seconds()
        
        return (f"VideoMetadata({w}×{h} @ {fps:.1f}fps, "
                f"{duration}s, {self.video_path})")
