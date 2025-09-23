"""
SAM-based image colorizer module
Handles segmentation and coloring of image regions
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
import base64
import logging

try:
    import torch
    from segment_anything import SamPredictor, sam_model_registry
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False
    torch = None
    SamPredictor = None
    sam_model_registry = None

logger = logging.getLogger(__name__)

class SAMColorizer:
    def __init__(self, sam_checkpoint_path: str = "sam_vit_h_4b8939.pth"):
        """Initialize SAM colorizer with model checkpoint"""
        if not SAM_AVAILABLE:
            raise ImportError("SAM dependencies not available")
            
        self.sam_predictor = None
        self.current_image = None
        self.original_image = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self._load_sam_model(sam_checkpoint_path)
            logger.info(f"SAM model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load SAM model: {e}")
            raise
    
    def _load_sam_model(self, checkpoint_path: str):
        """Load SAM model from checkpoint"""
        sam = sam_model_registry["vit_h"](checkpoint=checkpoint_path)
        sam.to(device=self.device)
        self.sam_predictor = SamPredictor(sam)
    
    def load_image(self, image_data: np.ndarray) -> bool:
        """Load image for processing"""
        try:
            self.original_image = image_data.copy()
            self.current_image = image_data.copy()
            
            # Set image for SAM predictor
            rgb_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
            self.sam_predictor.set_image(rgb_image)
            return True
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return False
    
    def segment_at_point(self, x: int, y: int) -> Optional[np.ndarray]:
        """Generate segmentation mask at clicked point"""
        try:
            input_point = np.array([[x, y]])
            input_label = np.array([1])
            
            masks, scores, _ = self.sam_predictor.predict(
                point_coords=input_point,
                point_labels=input_label,
                multimask_output=True,
            )
            
            # Return mask with highest score
            best_mask = masks[np.argmax(scores)]
            return best_mask
        except Exception as e:
            logger.error(f"Error in segmentation: {e}")
            return None
    
    def apply_color_to_mask(self, mask: np.ndarray, color: Tuple[int, int, int], alpha: float = 0.7) -> bool:
        """Apply color to masked region"""
        try:
            # Create colored overlay
            colored_mask = np.zeros_like(self.current_image)
            colored_mask[mask] = color
            
            # Blend with current image
            self.current_image = cv2.addWeighted(
                self.current_image, 1-alpha, colored_mask, alpha, 0
            )
            return True
        except Exception as e:
            logger.error(f"Error applying color: {e}")
            return False
    
    def color_at_point(self, x: int, y: int, color: Tuple[int, int, int]) -> bool:
        """Complete workflow: segment and color at point"""
        mask = self.segment_at_point(x, y)
        if mask is not None:
            return self.apply_color_to_mask(mask, color)
        return False
    
    def reset_image(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
    
    def get_current_image(self) -> Optional[np.ndarray]:
        """Get current processed image"""
        return self.current_image
    
    def image_to_base64(self, image: np.ndarray = None) -> str:
        """Convert image to base64 string"""
        if image is None:
            image = self.current_image
        
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"

class ImageProcessor:
    """Utility class for image processing operations"""
    
    @staticmethod
    def load_from_file(file_path: str) -> Optional[np.ndarray]:
        """Load image from file path"""
        try:
            image = cv2.imread(file_path)
            return image
        except Exception as e:
            logger.error(f"Error loading image from file: {e}")
            return None
    
    @staticmethod
    def load_from_upload(uploaded_file) -> Optional[np.ndarray]:
        """Load image from Django uploaded file"""
        try:
            # Read file content
            file_content = uploaded_file.read()
            uploaded_file.seek(0)  # Reset file pointer
            
            # Convert to numpy array
            nparr = np.frombuffer(file_content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"Error loading image from upload: {e}")
            return None
    
    @staticmethod
    def hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to BGR tuple"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (rgb[2], rgb[1], rgb[0])  # Convert RGB to BGR
    
    @staticmethod
    def save_image(image: np.ndarray, file_path: str) -> bool:
        """Save image to file"""
        try:
            cv2.imwrite(file_path, image)
            return True
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False