import base64
import os
import re
from typing import List, Dict, Any



# OpenAI client wrapper (supports new and legacy SDKs)
class OpenAIClient:
    def __init__(self):
        self._client = None
        self._mode = None
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                from django.conf import settings as dj_settings  # type: ignore
                api_key = getattr(dj_settings, "OPENAI_API_KEY", None)
            except Exception:
                api_key = None
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment or Django settings.")
        try:
            # New SDK style
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=api_key)
            self._mode = "new"
        except Exception:
            # Legacy SDK fallback
            import openai  # type: ignore
            openai.api_key = api_key
            self._client = openai
            self._mode = "legacy"

    def chat(self, model: str, messages: List[Dict[str, Any]], response_format: Dict[str, Any] = None) -> str:
        if self._mode == "new":
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": 0.6,
            }
            if response_format:
                kwargs["response_format"] = response_format
            resp = self._client.chat.completions.create(**kwargs)
        else:
            try:
                # Legacy SDK (<=0.x)
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.6,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                resp = self._client.ChatCompletion.create(**kwargs)
            except Exception:
                # Some environments expose the new-style endpoint on the module
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.6,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                resp = self._client.chat.completions.create(**kwargs)
        # Normalize return across SDKs
        try:
            return resp.choices[0].message.content or ""
        except Exception:
            return resp["choices"][0]["message"]["content"]


def file_to_data_url(upload) -> str:
    """Convert Django UploadedFile (image) to data URL for OpenAI vision input."""
    content_type = getattr(upload, "content_type", "application/octet-stream")
    data = upload.read()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


def build_messages(user_text: str, image_data_urls: List[str], doc_texts: List[str]) -> List[Dict[str, Any]]:
    system_prompt = (
        "You are PaintSense, a smart paint consultant.\n"
        "Given a user's room description, style preferences, and optional images of the space,\n"
        "recommend 3-5 paint color options with HEX codes (format: #RRGGBB), finishes (eggshell/matte/semi-gloss), and brief rationales.\n"
        "If images are provided, analyze the lighting, existing furniture colors, wall colors, and undertones.\n"
        "Be concise and practical. Always include HEX codes for each color recommendation.\n"
        "Close with preparation tips.\n"
        "Example format: 'Warm White (#F5F5DC) in eggshell finish would complement your space...'\n"
        "Please provide your response in JSON format with the recommendations.\n"
        "Recommendations should be per image."
    )

    # Build user message content
    content_parts = []
    
    # Add text content
    text_content = []
    if user_text:
        text_content.append(user_text)
    
    if doc_texts:
        joined = "\n\n".join(doc_texts)[:6000]  # keep prompt size reasonable
        text_content.append(f"Additional notes from documents:\n{joined}")
    
    if not text_content and not image_data_urls:
        text_content.append("Suggest paint colors for my space.")
    
    if text_content:
        content_parts.append({
            "type": "text",
            "text": "\n\n".join(text_content)
        })
    
    # Add images for vision API
    if image_data_urls:
        for image_url in image_data_urls:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content_parts if content_parts else "Suggest paint colors for my space."}
    ]


def extract_hex_codes(text: str) -> List[str]:
    return list(dict.fromkeys(re.findall(r"#[0-9a-fA-F]{6}", text)))[:8]



def run_agent(user_text: str, image_uploads: List[Any], doc_uploads: List[Any]) -> Dict[str, Any]:
    """
    Orchestrate the process: summarize inputs, confirm summary, and generate paint suggestions.
    Returns dict with 'reply' and 'swatches' (list of hex codes).
    """
    client = OpenAIClient()

    # Convert images to data URLs
    image_data_urls: List[str] = []
    for img in image_uploads:
        try:
            # Handle file objects
            if hasattr(img, "content_type") and getattr(img, "content_type", "").startswith("image/"):
                image_data_urls.append(file_to_data_url(img))
            # Handle string URLs (data URLs or regular URLs)
            elif isinstance(img, str) and (img.startswith("data:image/") or img.startswith("http")):
                image_data_urls.append(img)
        finally:
            # Only seek if it's a file object
            if hasattr(img, "seek"):
                img.seek(0)

    # Read document texts
    doc_texts: List[str] = []
    for doc in doc_uploads:
        try:
            name = getattr(doc, "name", "doc")
            if name.lower().endswith((".txt", ".md")):
                raw = doc.read().decode("utf-8", errors="ignore")
                doc_texts.append(raw[:8000])
            else:
                # Unsupported types for now
                pass
        finally:
            doc.seek(0)

    # Use vision model if images are provided, otherwise use regular model
    if image_data_urls:
        model = os.environ.get("PAINTSENSE_MODEL", "gpt-4o")  # Vision capable model
    else:
        model = os.environ.get("PAINTSENSE_MODEL", "gpt-4o-mini")
    
    # Generate paint suggestions directly
    response_format = { "type": "json_object" }
    messages = build_messages(user_text=user_text, image_data_urls=image_data_urls, doc_texts=doc_texts)
    reply = client.chat(model=model, messages=messages, response_format=response_format)
    swatches = extract_hex_codes(reply)
    

    return {
        "reply": reply,
        "swatches": swatches,
    }
    

def summrise_input(user_text: str, image_uploads: List[Any], doc_uploads: List[Any]) -> Dict[str, Any]:
    """Summarize user inputs with focus on room details."""
    # Modify the user text to request summarization
    reply = '{"reply":[{"image":"image1","room_description":"The room is a modern bedroom with a sleek design. It features a teal bed and matching chair, with striped wallpaper and green accents. The room has a polished floor, minimalistic furniture, and decorative elements like a basketball and framed pictures."},{"image":"image2","room_description":"This is a cozy living room with light yellow walls and a traditional style. The furniture is upholstered in beige and covered with patterned white and gray covers. The room has a few decorative pictures, curtains with a black and white pattern, and a small plant on the coffee table."},{"image":"image3","room_description":"The kitchen is designed in a contemporary style with a combination of white and rich red cabinetry. It features a light countertop with a speckled pattern, and the walls have a neutral tone. The kitchen is organized with hanging utensils, potted plants, and open shelving for storage."}]}'
    return {
        "reply": reply,
        "swatches": []
    }
    summary_request = f"Please elaborate and summarize the following room description: {user_text}" + "retrun response in json format {'reply':{image: string,room_description:string}}"
    return run_agent(user_text=summary_request, image_uploads=image_uploads, doc_uploads=doc_uploads)


def paint_suggestion(user_text: str, image_uploads: List[Any], doc_uploads: List[Any]) -> Dict[str, Any]:
    """Generate paint color suggestions based on user input."""
    # The run_agent function already has the paint consultant system prompt built-in
    reply = {"recommendations": [{"image": 1,"colors": [{"color": "Soft White","hex": "#F0F4F8","finish": "eggshell","rationale": "Soft White will brighten the room and provide a clean contrast to the bold turquoise elements, making them pop."},{"color": "Coral Pink","hex": "#FF6F61","finish": "matte","rationale": "Coral Pink adds warmth and a playful touch that complements the turquoise without overwhelming the space."},{"color": "Charcoal Gray","hex": "#333333","finish": "semi-gloss","rationale": "Charcoal Gray can add depth and sophistication, creating a modern edge against the vibrant colors."}]},{"image": 2,"colors": [{"color": "Creamy Beige","hex": "#E6D9C9","finish": "eggshell","rationale": "Creamy Beige will enhance the warm tones already present and create a seamless flow with the furniture."},{"color": "Warm Taupe","hex": "#C2B280","finish": "matte","rationale": "Warm Taupe adds a subtle contrast to the yellow walls while maintaining a cozy and inviting atmosphere."},{"color": "Soft Sage Green","hex": "#B7C9A3","finish": "matte","rationale": "Soft Sage Green introduces a refreshing element that complements the warm tones and adds a natural touch."}]},{"image": 3,"colors": [{"color": "Pale Gray","hex": "#D3D3D3","finish": "eggshell","rationale": "Pale Gray will provide a neutral backdrop that balances the bold red cabinetry and light countertops."},{"color": "Dusty Rose","hex": "#D6A8B4","finish": "matte","rationale": "Dusty Rose adds a soft, warm accent that harmonizes with the richness of the cabinetry without clashing."},{"color": "Muted Olive","hex": "#A8B95B","finish": "matte","rationale": "Muted Olive introduces a natural element that pairs well with the red cabinetry and adds depth to the space."}]}],"preparationtips": "Ensure surfaces are clean and free of dust. Use painters tape to protect edges and achieve clean lines. Test colors on small sections of the wall before fully committing."}

    return {
        "reply": reply,
        "swatches": []
    }

    user_text = user_text + "\n\n" + "Please provide your response in JSON format with the recommendations. as follows:\n\n"+ '"recommendations": [ {"image": "small description eg bed room, kitchen etc","colors": [{"color": "string","hex": "string","finish": "string","rationale": "string"}]}],"preparationtips": "string"'              
    return run_agent(user_text=user_text, image_uploads=image_uploads, doc_uploads=doc_uploads)    
