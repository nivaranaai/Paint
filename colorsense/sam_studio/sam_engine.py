"""
SAM Interactive Paint Studio Engine
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, List
import base64
import logging
import uuid
from threading import Lock

try:
    import torch
    from segment_anything import SamPredictor, sam_model_registry
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False

logger = logging.getLogger(__name__)

class SAMPaintStudio:
    def __init__(self, sam_checkpoint_path: str = "sam_vit_h_4b8939.pth"):
        if not SAM_AVAILABLE:
            raise ImportError("SAM dependencies not available")
            
        self.sam_predictor = None
        self.current_image = None
        self.original_image = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.color_history = []
        self.mask_cache = {}
        self.lock = Lock()
        self.sam_available = False
        
        try:
            self._load_sam_model(sam_checkpoint_path)
            self.sam_available = True
        except Exception as e:
            logger.warning(f"SAM model not available: {e}. Using fallback segmentation.")
            self.sam_available = False
    
    def _load_sam_model(self, checkpoint_path: str):
        import os
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"SAM model not found: {checkpoint_path}")
        sam = sam_model_registry["vit_h"](checkpoint=checkpoint_path)
        sam.to(device=self.device)
        self.sam_predictor = SamPredictor(sam)
    
    def load_image(self, image_data: np.ndarray) -> bool:
        with self.lock:
            self.original_image = image_data.copy()
            self.current_image = image_data.copy()
            
            if self.sam_available:
                rgb_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                self.sam_predictor.set_image(rgb_image)
            
            self.color_history.clear()
            self.mask_cache.clear()
            return True
    
    def get_segment_preview(self, x: int, y: int) -> Optional[Dict]:
        try:
            cache_key = f"{x}_{y}"
            if cache_key in self.mask_cache:
                mask = self.mask_cache[cache_key]
            else:
                if self.sam_available:
                    input_point = np.array([[x, y]])
                    input_label = np.array([1])
                    
                    masks, scores, _ = self.sam_predictor.predict(
                        point_coords=input_point,
                        point_labels=input_label,
                        multimask_output=True,
                    )
                    
                    mask = masks[np.argmax(scores)]
                else:
                    mask = self._flood_fill_segment(x, y)
                
                self.mask_cache[cache_key] = mask
            
            preview = self.current_image.copy()
            highlight_overlay = np.zeros_like(preview)
            highlight_overlay[mask] = [0, 255, 255]
            
            preview = cv2.addWeighted(preview, 0.8, highlight_overlay, 0.2, 0)
            
            return {
                "mask": mask,
                "preview": self.image_to_base64(preview),
                "area": int(np.sum(mask))
            }
        except Exception as e:
            logger.error(f"Preview error: {e}")
            return None
    
    def apply_color_to_segment(self, x: int, y: int, color: Tuple[int, int, int], 
                             blend_mode: str = "normal", opacity: float = 0.7) -> bool:
        try:
            cache_key = f"{x}_{y}"
            if cache_key in self.mask_cache:
                mask = self.mask_cache[cache_key]
            else:
                preview_result = self.get_segment_preview(x, y)
                if not preview_result:
                    return False
                mask = preview_result["mask"]
            
            colored_mask = np.zeros_like(self.current_image)
            colored_mask[mask] = color
            
            if blend_mode == "multiply":
                self.current_image[mask] = (self.current_image[mask] * colored_mask[mask] / 255).astype(np.uint8)
            elif blend_mode == "overlay":
                self.current_image = cv2.addWeighted(self.current_image, 1-opacity, colored_mask, opacity, 0)
            else:
                self.current_image[mask] = cv2.addWeighted(
                    self.current_image[mask], 1-opacity, 
                    colored_mask[mask], opacity, 0
                )
            
            self.color_history.append({
                "x": x, "y": y, "color": color, 
                "blend_mode": blend_mode, "opacity": opacity,
                "mask_area": int(np.sum(mask))
            })
            
            return True
        except Exception as e:
            logger.error(f"Color application error: {e}")
            return False
    
    def _flood_fill_segment(self, x: int, y: int) -> np.ndarray:
        h, w = self.current_image.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        
        cv2.floodFill(self.current_image.copy(), mask, (x, y), (255, 255, 255), 
                     loDiff=(20, 20, 20), upDiff=(20, 20, 20))
        
        return mask[1:-1, 1:-1].astype(bool)
    
    def get_color_palette(self, num_colors: int = 8) -> List[Tuple[int, int, int]]:
        try:
            data = self.original_image.reshape((-1, 3))
            data = np.float32(data)
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            centers = np.uint8(centers)
            return [tuple(map(int, color)) for color in centers]
        except:
            return [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
                   (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0)]
    
    def reset_image(self):
        with self.lock:
            if self.original_image is not None:
                self.current_image = self.original_image.copy()
                self.color_history.clear()
                self.mask_cache.clear()
    
    def image_to_base64(self, image: np.ndarray = None) -> str:
        if image is None:
            image = self.current_image
        
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return base64.b64encode(buffer).decode('utf-8')

class StudioSessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = Lock()
    
    def create_session(self, image_data: np.ndarray) -> str:
        session_id = str(uuid.uuid4())
        studio = SAMPaintStudio()
        
        if studio.load_image(image_data):
            with self.lock:
                self.sessions.clear()
                self.sessions[session_id] = studio
            return session_id
        return None
    
    def get_session(self, session_id: str) -> Optional[SAMPaintStudio]:
        with self.lock:
            return self.sessions.get(session_id)

session_manager = StudioSessionManager()