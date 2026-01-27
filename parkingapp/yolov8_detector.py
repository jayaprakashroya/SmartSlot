"""
YOLOv8 Vehicle Detection and License Plate Recognition Integration
This module provides real-time vehicle detection and license plate recognition
using YOLOv8 and EasyOCR for automatic parking management.
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Tuple, Optional
import threading
import time

# YOLOv8 imports
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("YOLOv8 not installed. Run: pip install ultralytics")

# EasyOCR imports
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not installed. Run: pip install easyocr")

logger = logging.getLogger(__name__)


class VehicleDetector:
    """
    Real-time vehicle detection using YOLOv8.
    Detects cars, trucks, and other vehicles in video streams.
    """

    def __init__(self, model_name: str = "yolov8m.pt", confidence_threshold: float = 0.35):
        """
        Initialize the vehicle detector.

        Args:
            model_name: YOLOv8 model name (medium=m for best parking detection accuracy)
            confidence_threshold: Minimum confidence score for detections (default: 0.35 optimized for parking lots)
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.model_name = model_name

        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_name)
                logger.info(f"YOLOv8 model '{model_name}' loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load YOLOv8 model: {e}")
        else:
            logger.error("YOLOv8 not available")

    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect vehicles in a frame.

        Args:
            frame: OpenCV image frame (BGR format)

        Returns:
            List of detection dictionaries with:
            - box: [x1, y1, x2, y2] coordinates
            - confidence: Detection confidence score
            - class_name: Object class (e.g., 'car', 'truck')
            - center: (x, y) center point
        """
        if self.model is None:
            return []

        try:
            # Run detection with optimized parameters for parking lot detection
            # imgsz=1280: Critical for aerial parking lot views - detects small distant vehicles
            # iou=0.40: Lower NMS threshold for parking lots (fewer duplicate detections)
            # conf=0.35: Optimized confidence for parking lot accuracy
            # device='cpu': Prevent GPU memory issues
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                imgsz=1280,
                iou=0.40,
                device='cpu',
                verbose=False
            )

            detections = []
            for result in results:
                for box in result.boxes:
                    # Extract box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])

                    # Class names for vehicle types
                    class_names = {
                        2: "car",
                        3: "motorcycle",
                        5: "bus",
                        7: "truck",
                    }

                    class_name = class_names.get(cls, "vehicle")

                    # Calculate center point
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2

                    detections.append(
                        {
                            "box": [x1, y1, x2, y2],
                            "confidence": conf,
                            "class_name": class_name,
                            "center": (center_x, center_y),
                            "area": (x2 - x1) * (y2 - y1),
                        }
                    )

            logger.debug(f"Detected {len(detections)} vehicles")
            return detections

        except Exception as e:
            logger.error(f"Vehicle detection error: {e}")
            return []

    def draw_detections(
        self, frame: np.ndarray, detections: List[Dict], show_confidence: bool = True
    ) -> np.ndarray:
        """
        Draw detection boxes on frame.

        Args:
            frame: Original frame
            detections: List of detections from detect_vehicles()
            show_confidence: Whether to display confidence scores

        Returns:
            Frame with drawn detections
        """
        frame_copy = frame.copy()
        colors = {
            "car": (0, 255, 0),
            "truck": (255, 0, 0),
            "motorcycle": (0, 0, 255),
            "bus": (255, 255, 0),
        }

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            class_name = det["class_name"]
            conf = det["confidence"]

            color = colors.get(class_name, (0, 255, 0))

            # Draw bounding box
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = f"{class_name}"
            if show_confidence:
                label += f" {conf:.2f}"

            cv2.putText(
                frame_copy,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        return frame_copy


class LicensePlateOCR:
    """
    License plate detection and OCR using EasyOCR.
    Extracts text from license plates in vehicle images.
    """

    def __init__(self, languages: List[str] = ["en"]):
        """
        Initialize the OCR reader.

        Args:
            languages: List of language codes to recognize
        """
        self.reader = None
        self.languages = languages

        if EASYOCR_AVAILABLE:
            try:
                self.reader = easyocr.Reader(languages, gpu=False)
                logger.info(f"EasyOCR reader initialized for languages: {languages}")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
        else:
            logger.error("EasyOCR not available")

    def extract_license_plate(self, frame: np.ndarray, vehicle_box: List[int]) -> Optional[str]:
        """
        Extract license plate text from vehicle region.

        Args:
            frame: Full frame image
            vehicle_box: Vehicle bounding box [x1, y1, x2, y2]

        Returns:
            Extracted license plate text or None
        """
        if self.reader is None:
            return None

        try:
            x1, y1, x2, y2 = vehicle_box

            # Extract vehicle region
            # Focus on lower portion of vehicle where license plate is typically located
            plate_y1 = max(0, y2 - int((y2 - y1) * 0.3))
            plate_y2 = y2
            plate_region = frame[plate_y1:plate_y2, x1:x2]

            if plate_region.size == 0:
                return None

            # Run OCR
            results = self.reader.readtext(plate_region)

            if not results:
                return None

            # Combine all recognized text
            plate_text = " ".join([text[1] for text in results])

            # Clean up text
            plate_text = plate_text.upper().strip()
            plate_text = "".join(c for c in plate_text if c.isalnum() or c == "-")

            if len(plate_text) >= 4:  # Minimum plate length
                logger.debug(f"Extracted license plate: {plate_text}")
                return plate_text

            return None

        except Exception as e:
            logger.error(f"License plate OCR error: {e}")
            return None

    def recognize_text(self, image_path: str) -> str:
        """
        Recognize text from an image file.

        Args:
            image_path: Path to image file

        Returns:
            Recognized text
        """
        if self.reader is None:
            return ""

        try:
            results = self.reader.readtext(image_path)
            text = "\n".join([result[1] for result in results])
            return text
        except Exception as e:
            logger.error(f"Text recognition error: {e}")
            return ""


def load_parking_spots_from_db(parking_lot_id: Optional[int] = None) -> List[Dict]:
    """
    Load parking spots from database instead of hardcoded values.
    This ensures the detector uses real parking spot positions.

    Args:
        parking_lot_id: Optional lot ID to filter spots

    Returns:
        List of parking spot dicts with format: 
        {'id': spot_id, 'x': x_pos, 'y': y_pos, 'width': width, 'height': height, 'number': spot_number}
    """
    try:
        from django.apps import apps
        if not apps.ready:
            logger.warning("Django not ready, using default parking spots")
            return []
        
        from .models import ParkingSpot
        
        # Query parking spots from database
        query = ParkingSpot.objects.all()
        
        if parking_lot_id:
            query = query.filter(parking_lot_id=parking_lot_id)
        
        spots = []
        for spot in query:
            spots.append({
                'id': str(spot.spot_id),
                'x': spot.x_position,
                'y': spot.y_position,
                'width': spot.spot_width,
                'height': spot.spot_height,
                'number': spot.spot_number,
                'lot_id': spot.parking_lot_id
            })
        
        logger.info(f"Loaded {len(spots)} parking spots from database")
        return spots
        
    except Exception as e:
        logger.error(f"Error loading parking spots from database: {e}")
        return []


class ParkingSpotTracker:
    """
    Tracks vehicles in specific parking spots using YOLOv8 detections.
    Maps detected vehicles to assigned parking spots.
    """

    def __init__(self, parking_spots: List[Dict]):
        """
        Initialize tracker with parking spot coordinates.

        Args:
            parking_spots: List of dicts with 'id', 'x', 'y', 'width', 'height'
        """
        self.parking_spots = parking_spots
        self.spot_vehicles = {}  # Map spot_id -> detected vehicle info
        self.vehicle_history = {}  # Track vehicle movements
        self.detector = VehicleDetector()
        self.ocr = LicensePlateOCR()

    def track_frame(self, frame: np.ndarray) -> Dict:
        """
        Track vehicles in a frame for all parking spots.

        Args:
            frame: Video frame

        Returns:
            Dictionary with tracking results
        """
        detections = self.detector.detect_vehicles(frame)
        results = {
            "timestamp": datetime.now(),
            "total_detections": len(detections),
            "spot_status": {},
        }

        for spot in self.parking_spots:
            spot_id = spot["id"]
            sx, sy, sw, sh = spot["x"], spot["y"], spot["width"], spot["height"]

            # Check which vehicles are in this spot using overlap-based detection
            # This is more accurate than center-point checking for parking spot detection
            vehicles_in_spot = []

            for det in detections:
                vx1, vy1, vx2, vy2 = det["box"]
                
                # Calculate intersection area between detection and spot
                x_left = max(vx1, sx)
                y_top = max(vy1, sy)
                x_right = min(vx2, sx + sw)
                y_bottom = min(vy2, sy + sh)
                
                # If rectangles intersect
                if x_right > x_left and y_bottom > y_top:
                    overlap_area = (x_right - x_left) * (y_bottom - y_top)
                    spot_area = sw * sh
                    overlap_ratio = overlap_area / spot_area
                    
                    # 20% overlap threshold optimized for parking lots
                    # More sensitive to catch vehicles better (lowered from 25%)
                    if overlap_ratio > 0.20:
                        vehicles_in_spot.append(det)

            if vehicles_in_spot:
                # Get the largest detection in the spot
                main_vehicle = max(vehicles_in_spot, key=lambda x: x["area"])

                # Try to extract license plate
                license_plate = self.ocr.extract_license_plate(frame, main_vehicle["box"])

                spot_status = {
                    "occupied": True,
                    "vehicle_class": main_vehicle["class_name"],
                    "confidence": main_vehicle["confidence"],
                    "license_plate": license_plate,
                }

                self.spot_vehicles[spot_id] = spot_status
            else:
                spot_status = {"occupied": False, "license_plate": None}
                self.spot_vehicles[spot_id] = spot_status

            results["spot_status"][spot_id] = spot_status

        return results

    def get_spot_status(self, spot_id: str) -> Dict:
        """Get current status of a parking spot."""
        return self.spot_vehicles.get(spot_id, {"occupied": False, "license_plate": None})
    
    def update_database_from_detections(self, results: Dict) -> None:
        """
        Update database with detection results to mark spots as occupied/empty.
        Uses robust sync manager to ensure reliability.
        
        Args:
            results: Dictionary from track_frame() containing spot_status
        """
        try:
            from django.apps import apps
            if not apps.ready:
                return
            
            from sync_detection_to_db import DetectionSyncManager
            
            spot_status = results.get("spot_status", {})
            
            # Convert spot_status to sync format
            detections_to_sync = {}
            for spot_id_str, status in spot_status.items():
                detections_to_sync[spot_id_str] = {
                    'occupied': status.get('occupied', False),
                    'plate': status.get('license_plate', None),
                    'confidence': status.get('confidence', 0.0)
                }
            
            # Find a parking lot to sync to (use first spot's lot)
            if detections_to_sync:
                try:
                    from .models import ParkingSpot
                    first_spot_id = int(list(detections_to_sync.keys())[0])
                    spot = ParkingSpot.objects.get(spot_id=first_spot_id)
                    lot_id = spot.parking_lot_id
                    
                    # Sync to database using robust manager
                    DetectionSyncManager.sync_spot_detections(lot_id, detections_to_sync)
                    
                except Exception as e:
                    logger.warning(f"Could not auto-detect lot_id: {e}")
                    
        except ImportError:
            logger.warning("DetectionSyncManager not available, using fallback sync")
            self._fallback_database_update(results)
        except Exception as e:
            logger.error(f"Error updating database from detections: {e}")
    
    def _fallback_database_update(self, results: Dict) -> None:
        """Fallback database update if sync manager unavailable"""
        try:
            from django.apps import apps
            if not apps.ready:
                return
            
            from .models import ParkingSpot, ParkedVehicle, Vehicle
            from django.utils import timezone
            
            spot_status = results.get("spot_status", {})
            
            for spot_id_str, status in spot_status.items():
                try:
                    spot_id = int(spot_id_str)
                    spot = ParkingSpot.objects.get(spot_id=spot_id)
                    
                    is_occupied = status.get("occupied", False)
                    confidence = status.get("confidence", 0.0)
                    license_plate = status.get("license_plate", "UNKNOWN")
                    
                    # Get current active parking record
                    active_parking = ParkedVehicle.objects.filter(
                        parking_spot=spot,
                        checkout_time__isnull=True
                    ).first()
                    
                    if is_occupied:
                        # Spot is occupied - create or update parking record
                        if not active_parking:
                            # Create new parking record
                            plate = license_plate if license_plate and license_plate != "UNKNOWN" else f"DETECTED_{spot_id}"
                            
                            # Get or create vehicle
                            vehicle, _ = Vehicle.objects.get_or_create(
                                license_plate=plate,
                                defaults={
                                    'vehicle_type': status.get("vehicle_class", "unknown"),
                                    'color': 'unknown'
                                }
                            )
                            
                            # Create parking record
                            ParkedVehicle.objects.create(
                                vehicle=vehicle,
                                parking_spot=spot,
                                checkin_time=timezone.now(),
                                detection_confidence=confidence
                            )
                            logger.info(f"Spot {spot.spot_number}: OCCUPIED - Confidence {confidence:.2f}")
                    else:
                        # Spot is empty - check out any active vehicles
                        if active_parking:
                            active_parking.checkout_time = timezone.now()
                            active_parking.save()
                            logger.info(f"Spot {spot.spot_number}: EMPTY - Vehicle checked out")
                
                except (ValueError, ParkingSpot.DoesNotExist):
                    continue
                except Exception as e:
                    logger.error(f"Error updating spot {spot_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating database from detections: {e}")


class ParkingVideoProcessor:
    """
    Real-time parking lot video processing.
    Processes video stream and updates parking system.
    """

    def __init__(self, video_source: str = 0, parking_spots: Optional[List[Dict]] = None, parking_lot_id: Optional[int] = None):
        """
        Initialize video processor.

        Args:
            video_source: Video file path or camera index (0 for default camera)
            parking_spots: List of parking spot definitions (if not provided, loads from database)
            parking_lot_id: Optional lot ID to load specific lot's parking spots from database
        """
        self.video_source = video_source
        
        # If parking spots not provided, try to load from database
        if parking_spots is None:
            self.parking_spots = load_parking_spots_from_db(parking_lot_id)
            if not self.parking_spots:
                logger.warning("No parking spots loaded from database, using default grid layout")
                self.parking_spots = []
        else:
            self.parking_spots = parking_spots
        self.tracker = ParkingSpotTracker(self.parking_spots)
        self.is_running = False
        self.processing_thread = None

    def process_video(self, callback=None):
        """
        Process video stream and call callback with results.

        Args:
            callback: Function to call with tracking results
        """
        try:
            cap = cv2.VideoCapture(self.video_source)

            if not cap.isOpened():
                logger.error(f"Failed to open video source: {self.video_source}")
                return

            self.is_running = True
            frame_count = 0
            fps_counter = 0
            fps_time = time.time()

            logger.info("Video processing started")

            while self.is_running:
                ret, frame = cap.read()

                if not ret:
                    logger.warning("Failed to read frame from video")
                    break

                frame_count += 1
                fps_counter += 1

                # Adaptive resize to preserve aspect ratio and quality
                # Maintains height at 720p max while preserving aspect ratio
                height, width = frame.shape[:2]
                target_height = 720 if height > 720 else height
                scale = target_height / height
                new_width = int(width * scale)
                frame = cv2.resize(frame, (new_width, target_height), interpolation=cv2.INTER_LINEAR)

                # Track vehicles in this frame
                results = self.tracker.track_frame(frame)
                
                # Update database with detection results (marks spots occupied/empty)
                self.tracker.update_database_from_detections(results)

                # Call callback with results
                if callback:
                    try:
                        callback(results)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                # Calculate and display FPS
                if time.time() - fps_time >= 1.0:
                    fps = fps_counter
                    fps_counter = 0
                    fps_time = time.time()
                    logger.info(f"Processing FPS: {fps}")

                # Small delay to prevent CPU overload
                time.sleep(0.01)

            cap.release()
            logger.info("Video processing stopped")

        except Exception as e:
            logger.error(f"Video processing error: {e}")
        finally:
            self.is_running = False

    def start_async(self, callback=None):
        """Start video processing in a background thread."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self.process_video, args=(callback,), daemon=True
            )
            self.processing_thread.start()

    def stop_async(self):
        """Stop background video processing."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)

    def process_image(self, image_path: str) -> Dict:
        """
        Process a single image.

        Args:
            image_path: Path to image file

        Returns:
            Detection results
        """
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                logger.error(f"Failed to load image: {image_path}")
                return {}

            return self.tracker.track_frame(frame)

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {}


# Utility functions

def setup_logging(log_level=logging.INFO):
    """Configure logging for YOLOv8 integration."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_parking_spots_from_grid(rows: int, cols: int, width: int, height: int) -> List[Dict]:
    """
    Create parking spot definitions for a grid layout.

    Args:
        rows: Number of rows
        cols: Number of columns
        width: Total width
        height: Total height

    Returns:
        List of parking spot definitions
    """
    spots = []
    spot_width = width // cols
    spot_height = height // rows

    for row in range(rows):
        for col in range(cols):
            spot_id = f"A{row + 1}{col + 1}"
            spots.append(
                {
                    "id": spot_id,
                    "x": col * spot_width,
                    "y": row * spot_height,
                    "width": spot_width,
                    "height": spot_height,
                }
            )

    return spots


if __name__ == "__main__":
    # Example usage
    setup_logging()

    # Create sample parking spots
    spots = create_parking_spots_from_grid(rows=3, cols=4, width=1280, height=720)

    # Initialize processor
    processor = ParkingVideoProcessor(video_source=0, parking_spots=spots)

    # Define callback for results
    def handle_results(results):
        print(f"\nFrame at {results['timestamp']}")
        print(f"Total detections: {results['total_detections']}")
        for spot_id, status in results["spot_status"].items():
            if status["occupied"]:
                plate = status.get("license_plate", "Unknown")
                print(f"  {spot_id}: OCCUPIED - Plate: {plate}")

    # Process video (Ctrl+C to stop)
    try:
        print("Starting video processing. Press Ctrl+C to stop.")
        processor.process_video(callback=handle_results)
    except KeyboardInterrupt:
        print("\nStopping video processing...")
