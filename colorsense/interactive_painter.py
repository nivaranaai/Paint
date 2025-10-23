import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import json
import logging

try:
    import torch
    from segment_anything import SamPredictor, sam_model_registry
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False

logger = logging.getLogger(__name__)

class InteractivePainter:
    def __init__(self, sam_checkpoint_path: str = "sam_vit_h_4b8939.pth"):
        self.sessions = {}
        self.sam_predictor = None
        self.sam_available = False
        
        if SAM_AVAILABLE:
            try:
                self._load_sam_model(sam_checkpoint_path)
                self.sam_available = True
                logger.info("SAM model loaded successfully")
            except Exception as e:
                logger.warning(f"SAM model not available: {e}. Using fallback segmentation.")
                self.sam_available = False
    
    def _load_sam_model(self, checkpoint_path: str):
        import os
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"SAM model not found: {checkpoint_path}")
        sam = sam_model_registry["vit_h"](checkpoint=checkpoint_path)
        sam.to(device="cuda" if torch.cuda.is_available() else "cpu")
        self.sam_predictor = SamPredictor(sam)
    
    def create_session(self, image_data, session_id):
        """Create a new painting session"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(image_bytes))
            image_array = np.array(image.convert('RGB'))
            
            # Convert RGB to BGR for OpenCV
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Store original and current images
            self.sessions[session_id] = {
                'original': image_bgr.copy(),
                'current': image_bgr.copy(),
                'rgb_original': image_array.copy(),
                'mask_cache': {},
                'mask_history': []
            }
            
            # Prepare SAM for this image
            if self.sam_available:
                self.sam_predictor.set_image(image_array)
            
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def paint_at_point(self, session_id, x, y, hex_color, brush_size=30):
        """Paint at specific coordinates with SAM segmentation"""
        if session_id not in self.sessions:
            return None
        
        try:
            session = self.sessions[session_id]
            current_image = session['current'].copy()
            
            # Convert hex to BGR
            hex_color = hex_color.lstrip('#')
            target_color_bgr = tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))  # BGR order
            
            # Get or generate mask
            cache_key = f"{x}_{y}"
            if cache_key in session['mask_cache']:
                mask = session['mask_cache'][cache_key]
            else:
                if self.sam_available:
                    # Use SAM for segmentation
                    input_point = np.array([[x, y]])
                    input_label = np.array([1])
                    
                    masks, scores, _ = self.sam_predictor.predict(
                        point_coords=input_point,
                        point_labels=input_label,
                        multimask_output=True,
                    )
                    
                    mask = masks[np.argmax(scores)]
                else:
                    # Fallback to flood fill
                    mask = self._flood_fill_segment(current_image, x, y)
                
                session['mask_cache'][cache_key] = mask
            
            # Apply color only to the masked region
            current_image[mask] = target_color_bgr
            
            # Store the painted image
            session['current'] = current_image
            
            # Convert BGR back to RGB for display
            rgb_image = cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error painting: {e}")
            return None
    
    def _flood_fill_segment(self, image, x, y):
        """Fallback segmentation using flood fill"""
        h, w = image.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        
        cv2.floodFill(image.copy(), mask, (x, y), (255, 255, 255), 
                     loDiff=(15, 15, 15), upDiff=(15, 15, 15))
        
        return mask[1:-1, 1:-1].astype(bool)
    
    def reset_session(self, session_id):
        """Reset to original image"""
        if session_id not in self.sessions:
            return None
        
        try:
            session = self.sessions[session_id]
            # Reset to original
            session['current'] = session['original'].copy()
            session['mask_cache'].clear()
            
            # Convert BGR back to RGB for display
            rgb_image = cv2.cvtColor(session['current'], cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error resetting: {e}")
            return None
    
    def get_current_image(self, session_id):
        """Get current painted image"""
        if session_id not in self.sessions:
            return None
        
        try:
            # Convert BGR back to RGB for display
            rgb_image = cv2.cvtColor(self.sessions[session_id]['current'], cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error getting image: {e}")
            return None

# Global painter instance
interactive_painter = InteractivePainter()