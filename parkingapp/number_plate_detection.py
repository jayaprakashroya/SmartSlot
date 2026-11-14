import easyocr
import cv2
from typing import List, Dict, Any, Optional

# Singleton EasyOCR reader to avoid reinitializing on each call
_OCR_READER: Optional[easyocr.Reader] = None


def _get_reader(use_gpu: bool = False) -> easyocr.Reader:
    global _OCR_READER
    if _OCR_READER is None:
        _OCR_READER = easyocr.Reader(['en'], gpu=use_gpu)
    return _OCR_READER


def detect_numberplate_in_image(img: Any, detail: int = 1) -> List[Dict[str, Any]]:
    """
    Detect text (license plates) in a BGR image (numpy array) using EasyOCR.

    Args:
        img: BGR image (numpy.ndarray)
        detail: Reader detail level (0/1) - 1 returns (bbox, text, prob)

    Returns:
        List of dicts: [{'bbox': bbox, 'text': text, 'prob': prob}, ...]
    """
    reader = _get_reader()
    # EasyOCR expects RGB images
    try:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception:
        rgb = img

    results = reader.readtext(rgb, detail=detail)
    plates = []
    for res in results:
        if len(res) == 3:
            bbox, text, prob = res
        else:
            # Fallback if structure differs
            bbox = res[0]
            text = res[1] if len(res) > 1 else ''
            prob = res[2] if len(res) > 2 else 0.0

        plates.append({'bbox': bbox, 'text': text, 'prob': float(prob)})

    return plates


def get_best_plate_text(plates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the plate dict with highest probability, or None."""
    if not plates:
        return None
    best = max(plates, key=lambda p: p.get('prob', 0.0))
    return best


def draw_plate_text(frame: Any, pos: tuple, text: str) -> None:
    """Draw detected plate text near the parking spot on the frame."""
    x, y = pos
    try:
        cv2.putText(frame, text, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
    except Exception:
        pass
