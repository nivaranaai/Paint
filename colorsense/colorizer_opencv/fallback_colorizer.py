"""
Fallback colorizer without SAM - uses flood fill
"""
import cv2
import numpy as np
import base64
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FallbackColorizer:
    def __init__(self):
        self.current_image = None
        self.original_image = None
    
    def load_image(self, image_data: np.ndarray) -> bool:
        try:
            self.original_image = image_data.copy()
            self.current_image = image_data.copy()
            return True
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return False
    
    def color_at_point(self, x: int, y: int, color: Tuple[int, int, int]) -> bool:
        try:
            h, w = self.current_image.shape[:2]
            mask = np.zeros((h+2, w+2), np.uint8)
            cv2.floodFill(self.current_image, mask, (x, y), color, 
                         loDiff=(15, 15, 15), upDiff=(15, 15, 15))
            return True
        except Exception as e:
            logger.error(f"Error coloring: {e}")
            return False
    
    def reset_image(self):
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
    
    def get_current_image(self) -> Optional[np.ndarray]:
        return self.current_image
    
    def image_to_base64(self, image: np.ndarray = None) -> str:
        if image is None:
            image = self.current_image
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"