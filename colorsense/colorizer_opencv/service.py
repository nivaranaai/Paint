"""
Service layer for image colorization
Manages colorizer instances and provides high-level API
"""
import os
import uuid
from typing import Dict, Optional, Tuple, Any
from django.conf import settings
from .sam_colorizer import SAMColorizer, ImageProcessor
import logging

logger = logging.getLogger(__name__)

class ColorizerService:
    """Service to manage colorizer sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, SAMColorizer] = {}
        self.sam_model_path = os.path.join(settings.BASE_DIR, "sam_vit_h_4b8939.pth")
    
    def create_session(self, image_file) -> Dict[str, Any]:
        """Create new colorizer session with uploaded image"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Load image
            image_data = ImageProcessor.load_from_upload(image_file)
            if image_data is None:
                return {"success": False, "error": "Failed to load image"}
            
            # Try SAM first, fallback to simple colorizer
            try:
                if SAMColorizer is None:
                    raise ImportError("SAM not available")
                colorizer = SAMColorizer(self.sam_model_path)
                if not colorizer.load_image(image_data):
                    raise Exception("SAM failed")
            except Exception as e:
                logger.warning(f"SAM failed, using fallback: {e}")
                from .fallback_colorizer import FallbackColorizer
                colorizer = FallbackColorizer()
                if not colorizer.load_image(image_data):
                    return {"success": False, "error": "Failed to initialize colorizer"}
            
            # Store session
            self._sessions[session_id] = colorizer
            
            # Return session info with base64 image
            return {
                "success": True,
                "session_id": session_id,
                "image": colorizer.image_to_base64(),
                "width": image_data.shape[1],
                "height": image_data.shape[0]
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {"success": False, "error": str(e)}
    
    def color_at_point(self, session_id: str, x: int, y: int, color: str) -> Dict[str, Any]:
        """Color image at specified point"""
        try:
            colorizer = self._sessions.get(session_id)
            if not colorizer:
                return {"success": False, "error": "Session not found"}
            
            # Convert hex color to BGR
            bgr_color = ImageProcessor.hex_to_bgr(color)
            
            # Apply coloring
            success = colorizer.color_at_point(x, y, bgr_color)
            if not success:
                return {"success": False, "error": "Failed to apply color"}
            
            # Return updated image
            return {
                "success": True,
                "image": colorizer.image_to_base64()
            }
            
        except Exception as e:
            logger.error(f"Error coloring at point: {e}")
            return {"success": False, "error": str(e)}
    
    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset session to original image"""
        try:
            colorizer = self._sessions.get(session_id)
            if not colorizer:
                return {"success": False, "error": "Session not found"}
            
            colorizer.reset_image()
            return {
                "success": True,
                "image": colorizer.image_to_base64()
            }
            
        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            return {"success": False, "error": str(e)}
    
    def get_session_image(self, session_id: str) -> Dict[str, Any]:
        """Get current session image"""
        try:
            colorizer = self._sessions.get(session_id)
            if not colorizer:
                return {"success": False, "error": "Session not found"}
            
            return {
                "success": True,
                "image": colorizer.image_to_base64()
            }
            
        except Exception as e:
            logger.error(f"Error getting session image: {e}")
            return {"success": False, "error": str(e)}
    
    def save_session_image(self, session_id: str, filename: str = None) -> Dict[str, Any]:
        """Save current session image to media folder"""
        try:
            colorizer = self._sessions.get(session_id)
            if not colorizer:
                return {"success": False, "error": "Session not found"}
            
            # Generate filename if not provided
            if not filename:
                filename = f"colored_{session_id[:8]}.jpg"
            
            # Save to media folder
            media_folder = os.path.join(settings.MEDIA_ROOT, "colored_images")
            os.makedirs(media_folder, exist_ok=True)
            
            file_path = os.path.join(media_folder, filename)
            current_image = colorizer.get_current_image()
            
            if ImageProcessor.save_image(current_image, file_path):
                file_url = f"{settings.MEDIA_URL}colored_images/{filename}"
                return {
                    "success": True,
                    "file_path": file_path,
                    "file_url": file_url
                }
            else:
                return {"success": False, "error": "Failed to save image"}
            
        except Exception as e:
            logger.error(f"Error saving session image: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up session resources"""
        try:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up session: {e}")
            return False
    
    def get_active_sessions(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)

# Global service instance
colorizer_service = ColorizerService()