from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .sam_engine import session_manager
from ..colorizer_opencv.sam_colorizer import ImageProcessor
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def create_studio_session(request):
    try:
        if 'image' not in request.FILES:
            return JsonResponse({"success": False, "error": "No image provided"}, status=400)
        
        image_file = request.FILES['image']
        image_data = ImageProcessor.load_from_upload(image_file)
        
        if image_data is None:
            return JsonResponse({"success": False, "error": "Invalid image"}, status=400)
        
        session_id = session_manager.create_session(image_data)
        if not session_id:
            return JsonResponse({"success": False, "error": "Failed to create session"}, status=500)
        
        studio = session_manager.get_session(session_id)
        palette = studio.get_color_palette()
        
        return JsonResponse({
            "success": True,
            "session_id": session_id,
            "image": studio.image_to_base64(),
            "palette": palette,
            "image_size": {"width": image_data.shape[1], "height": image_data.shape[0]},
            "sam_available": studio.sam_available
        })
        
    except Exception as e:
        logger.error(f"Studio session creation error: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_POST
def apply_color(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        x, y = int(data.get('x')), int(data.get('y'))
        color_hex = data.get('color', '#FF0000')
        blend_mode = data.get('blend_mode', 'normal')
        opacity = float(data.get('opacity', 0.7))
        
        studio = session_manager.get_session(session_id)
        if not studio:
            return JsonResponse({"success": False, "error": "Session not found"}, status=404)
        
        color_bgr = ImageProcessor.hex_to_bgr(color_hex)
        success = studio.apply_color_to_segment(x, y, color_bgr, blend_mode, opacity)
        
        if success:
            return JsonResponse({
                "success": True,
                "image": studio.image_to_base64(),
                "history_count": len(studio.color_history)
            })
        else:
            return JsonResponse({"success": False, "error": "Color application failed"}, status=400)
        
    except Exception as e:
        logger.error(f"Color application error: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def sam_studio_demo(request):
    return render(request, "colorsense/sam_studio.html")