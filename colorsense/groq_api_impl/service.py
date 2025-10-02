"""
Groq Service Layer
"""
from .groq_client import GroqClient, image_to_base64
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        try:
            # Use environment variable for API key
            self.client = GroqClient()
            self.default_chat_model = "llama-3.1-8b-instant"
            self.default_vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        except Exception as e:
            logger.error(f"Groq service initialization failed: {e}")
            self.client = None
    
    def simple_chat(self, message: str, model: str = None) -> Dict[str, Any]:
        """Simple text chat"""
        if not self.client:
            return {"success": False, "error": "Groq client not initialized"}
        
        try:
            model = model or self.default_chat_model
            messages = [{"role": "user", "content": message}]
            response = self.client.chat(model=model, messages=messages)
            
            return {
                "success": True,
                "response": response,
                "model": model
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def vision_analysis(self, text: str, image_file, model: str = None) -> Dict[str, Any]:
        """Analyze image with text"""
        if not self.client:
            return {"success": False, "error": "Groq client not initialized"}
        
        try:
            model = model or self.default_vision_model
            image_b64 = image_to_base64(image_file)
            
            if not image_b64:
                return {"success": False, "error": "Failed to process image"}
            
            response = self.client.vision_chat(
                model=model,
                text=text,
                image_base64=image_b64
            )
            
            return {
                "success": True,
                "response": response,
                "model": model
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def paint_consultation(self, room_description: str, image_file=None) -> Dict[str, Any]:
        """Paint consultation service"""
        try:
            prompt = f"""
            You are a professional paint consultant. Based on: "{room_description}"
            
            Provide:
            1. 3-5 paint color recommendations with HEX codes
            2. Finish suggestions (matte/eggshell/semi-gloss)
            3. Brief rationale for each color
            4. Preparation tips
            
            Format as JSON:
            {{
                "recommendations": [
                    {{"color": "Name", "hex": "#RRGGBB", "finish": "type", "rationale": "reason"}}
                ],
                "preparation_tips": "tips"
            }}
            """
            
            if image_file and self.default_vision_model:
                result = self.vision_analysis(prompt, image_file)
            else:
                if image_file:
                    prompt += "\n\nNote: Image uploaded but vision analysis unavailable."
                result = self.simple_chat(prompt)
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_models(self) -> List[str]:
        """Get available models"""
        if not self.client:
            return []
        return self.client.get_available_models()

groq_service = GroqService()