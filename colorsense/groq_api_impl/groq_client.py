"""
Groq API Client Implementation
"""
import base64
import os
from typing import List, Dict, Any
import logging

try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    import requests
    GROQ_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found - Groq functionality will be disabled")
            self.client = None
            return
        
        if GROQ_SDK_AVAILABLE:
            self.client = Groq(api_key=self.api_key)
        else:
            self.base_url = "https://api.groq.com/openai/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        
        self.available_models = [
            "llama-3.1-8b-instant", 
            "llama-3.3-70b-versatile", 
            "gemma2-9b-it",
            "meta-llama/llama-4-scout-17b-16e-instruct"
        ]
    
    def chat(self, model: str, messages: List[Dict[str, Any]], temperature: float = 0.7) -> str:
        """Send chat completion request"""
        if not self.api_key:
            return "Groq API key not configured"
        
        try:
            if GROQ_SDK_AVAILABLE:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=1024
                )
                return completion.choices[0].message.content
            else:
                import requests
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 1024
                }
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"Request failed: {str(e)}"
    
    def vision_chat(self, model: str, text: str, image_base64: str, temperature: float = 0.7) -> str:
        """Send vision chat request"""
        if not self.api_key:
            return "Groq API key not configured"
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            if GROQ_SDK_AVAILABLE:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=1024
                )
                return completion.choices[0].message.content
            else:
                import requests
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 1024
                }
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Vision Error: {response.status_code}"
                
        except Exception as e:
            return f"Vision request failed: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """Get available models"""
        if not self.api_key:
            return self.available_models
        
        try:
            if GROQ_SDK_AVAILABLE:
                models = self.client.models.list()
                return [model.id for model in models.data]
            else:
                import requests
                response = requests.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [model["id"] for model in data["data"]]
                else:
                    return self.available_models
                
        except Exception as e:
            return self.available_models

def image_to_base64(image_file) -> str:
    """Convert uploaded image to base64"""
    try:
        content = image_file.read()
        image_file.seek(0)
        return base64.b64encode(content).decode('utf-8')
    except Exception as e:
        logger.error(f"Error converting image: {e}")
        return ""