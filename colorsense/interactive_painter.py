import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import json

class InteractivePainter:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, image_data, session_id):
        """Create a new painting session"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(image_bytes))
            image_array = np.array(image.convert('RGB'))
            
            # Store original and current images
            self.sessions[session_id] = {
                'original': image_array.copy(),
                'current': image_array.copy(),
                'mask_history': []
            }
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def paint_at_point(self, session_id, x, y, hex_color, brush_size=30):
        """Paint at specific coordinates with intelligent region detection"""
        if session_id not in self.sessions:
            return None
        
        try:
            current_image = self.sessions[session_id]['current'].copy()
            h, w = current_image.shape[:2]
            
            # Convert hex to RGB
            hex_color = hex_color.lstrip('#')
            target_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Get clicked pixel color
            clicked_color = current_image[y, x]
            
            # Create mask for similar colors using flood fill
            mask = np.zeros((h + 2, w + 2), np.uint8)
            
            # Flood fill parameters - more tolerant for better region detection
            lo_diff = (20, 20, 20)
            up_diff = (20, 20, 20)
            
            # Perform flood fill
            cv2.floodFill(current_image, mask, (x, y), target_color, lo_diff, up_diff)
            
            # Store the painted image
            self.sessions[session_id]['current'] = current_image
            
            # Convert back to base64
            pil_image = Image.fromarray(current_image)
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error painting: {e}")
            return None
    
    def reset_session(self, session_id):
        """Reset to original image"""
        if session_id not in self.sessions:
            return None
        
        try:
            # Reset to original
            self.sessions[session_id]['current'] = self.sessions[session_id]['original'].copy()
            
            # Convert to base64
            pil_image = Image.fromarray(self.sessions[session_id]['current'])
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
            pil_image = Image.fromarray(self.sessions[session_id]['current'])
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error getting image: {e}")
            return None

# Global painter instance
interactive_painter = InteractivePainter()