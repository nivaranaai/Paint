"""
Enhanced Interactive Paint Studio with SAM Integration
Combines carousel functionality with AI segmentation and paint recommendations
"""
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import json
import uuid
from threading import Lock

try:
    import torch
    from segment_anything import SamPredictor, sam_model_registry
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False

class EnhancedPaintStudio:
    def __init__(self, sam_checkpoint_path: str = "sam_vit_h_4b8939.pth"):
        self.sessions = {}
        self.lock = Lock()
        self.sam_predictor = None
        self.sam_available = False
        
        if SAM_AVAILABLE:
            try:
                self._load_sam_model(sam_checkpoint_path)
                self.sam_available = True
            except Exception as e:
                print(f"SAM model not available: {e}")
                self.sam_available = False
    
    def _load_sam_model(self, checkpoint_path: str):
        import os
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"SAM model not found: {checkpoint_path}")
        sam = sam_model_registry["vit_h"](checkpoint=checkpoint_path)
        sam.to(device="cuda" if torch.cuda.is_available() else "cpu")
        self.sam_predictor = SamPredictor(sam)
    
    def create_carousel_session(self, images_data, paint_recommendations, session_id=None):
        """Create session with multiple images and paint recommendations"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        try:
            processed_images = []
            
            for img_data in images_data:
                # Decode base64 image
                if isinstance(img_data, str) and img_data.startswith('data:'):
                    image_bytes = base64.b64decode(img_data.split(',')[1])
                else:
                    image_bytes = base64.b64decode(img_data)
                
                image = Image.open(BytesIO(image_bytes))
                image_array = np.array(image.convert('RGB'))
                
                # Convert RGB to BGR for OpenCV
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                
                processed_images.append({
                    'original': image_bgr.copy(),
                    'current': image_bgr.copy(),
                    'rgb_original': image_array.copy(),
                    'mask_cache': {},
                    'color_history': []
                })
            
            with self.lock:
                self.sessions[session_id] = {
                    'images': processed_images,
                    'current_index': 0,
                    'paint_recommendations': paint_recommendations,
                    'sam_ready': {}
                }
            
            # Prepare SAM for first image
            if self.sam_available and processed_images:
                self._prepare_sam_for_image(session_id, 0)
            
            return session_id
            
        except Exception as e:
            print(f"Error creating carousel session: {e}")
            return None
    
    def _prepare_sam_for_image(self, session_id, image_index):
        """Prepare SAM predictor for specific image"""
        if not self.sam_available or session_id not in self.sessions:
            return
        
        try:
            session = self.sessions[session_id]
            if image_index < len(session['images']):
                rgb_image = session['images'][image_index]['rgb_original']
                self.sam_predictor.set_image(rgb_image)
                session['sam_ready'][image_index] = True
        except Exception as e:
            print(f"Error preparing SAM: {e}")
    
    def switch_image(self, session_id, direction):
        """Switch to next/previous image in carousel"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_idx = session['current_index']
        
        if direction == 'next':
            new_idx = (current_idx + 1) % len(session['images'])
        else:  # previous
            new_idx = (current_idx - 1) % len(session['images'])
        
        session['current_index'] = new_idx
        
        # Prepare SAM for new image
        if self.sam_available and new_idx not in session['sam_ready']:
            self._prepare_sam_for_image(session_id, new_idx)
        
        return self.get_current_image_data(session_id)
    
    def get_segment_preview(self, session_id, x, y):
        """Generate segment preview at point"""
        if session_id not in self.sessions:
            return None
        
        try:
            session = self.sessions[session_id]
            current_idx = session['current_index']
            current_image = session['images'][current_idx]
            
            cache_key = f"{x}_{y}"
            if cache_key in current_image['mask_cache']:
                mask = current_image['mask_cache'][cache_key]
            else:
                if self.sam_available and current_idx in session['sam_ready']:
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
                    mask = self._flood_fill_segment(current_image['current'], x, y)
                
                current_image['mask_cache'][cache_key] = mask
            
            # Create preview with highlight
            preview = current_image['current'].copy()
            highlight_overlay = np.zeros_like(preview)
            highlight_overlay[mask] = [0, 255, 255]  # Yellow highlight
            
            preview = cv2.addWeighted(preview, 0.8, highlight_overlay, 0.2, 0)
            
            return {
                "mask": mask,
                "preview": self._image_to_base64(preview),
                "area": int(np.sum(mask))
            }
            
        except Exception as e:
            print(f"Preview error: {e}")
            return None
    
    def apply_recommended_color(self, session_id, x, y, color_hex, blend_mode="normal", opacity=0.7):
        """Apply recommended color to segment"""
        if session_id not in self.sessions:
            return None
        
        try:
            session = self.sessions[session_id]
            current_idx = session['current_index']
            current_image = session['images'][current_idx]
            
            # Get or generate mask
            cache_key = f"{x}_{y}"
            if cache_key in current_image['mask_cache']:
                mask = current_image['mask_cache'][cache_key]
            else:
                preview_result = self.get_segment_preview(session_id, x, y)
                if not preview_result:
                    return None
                mask = preview_result["mask"]
                current_image['mask_cache'][cache_key] = mask
            
            # Convert hex to BGR
            color_bgr = self._hex_to_bgr(color_hex)
            
            # Apply color with blending only to masked area
            colored_mask = np.zeros_like(current_image['current'])
            colored_mask[mask] = color_bgr
            
            if blend_mode == "multiply":
                current_image['current'][mask] = (current_image['current'][mask] * colored_mask[mask] / 255).astype(np.uint8)
            elif blend_mode == "overlay":
                current_image['current'][mask] = cv2.addWeighted(
                    current_image['current'][mask], 1-opacity, 
                    colored_mask[mask], opacity, 0
                )
            else:  # normal
                current_image['current'][mask] = cv2.addWeighted(
                    current_image['current'][mask], 1-opacity, 
                    colored_mask[mask], opacity, 0
                )
            
            # Store in history
            current_image['color_history'].append({
                "x": x, "y": y, "color": color_hex, 
                "blend_mode": blend_mode, "opacity": opacity,
                "mask_area": int(np.sum(mask))
            })
            
            return self.get_current_image_data(session_id)
            
        except Exception as e:
            print(f"Color application error: {e}")
            return None
    
    def _flood_fill_segment(self, image, x, y):
        """Fallback segmentation using flood fill"""
        h, w = image.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        
        # Use flood fill with tolerance for better segmentation
        cv2.floodFill(image.copy(), mask, (x, y), (255, 255, 255), 
                     loDiff=(15, 15, 15), upDiff=(15, 15, 15))
        
        # Return the mask without padding as boolean
        return mask[1:-1, 1:-1].astype(bool)
    
    def _hex_to_bgr(self, hex_color):
        """Convert hex color to BGR tuple"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (rgb[2], rgb[1], rgb[0])  # Convert RGB to BGR
    
    def _image_to_base64(self, image):
        """Convert image to base64 string"""
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return base64.b64encode(buffer).decode('utf-8')
    
    def get_current_image_data(self, session_id):
        """Get current image and session data"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_idx = session['current_index']
        current_image = session['images'][current_idx]
        
        return {
            "image": self._image_to_base64(current_image['current']),
            "index": current_idx,
            "total": len(session['images']),
            "recommendations": session['paint_recommendations'],
            "sam_available": self.sam_available,
            "history_count": len(current_image['color_history'])
        }
    
    def reset_current_image(self, session_id):
        """Reset current image to original"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_idx = session['current_index']
        current_image = session['images'][current_idx]
        
        current_image['current'] = current_image['original'].copy()
        current_image['color_history'].clear()
        current_image['mask_cache'].clear()
        
        return self.get_current_image_data(session_id)

# Global enhanced painter instance
enhanced_painter = EnhancedPaintStudio()