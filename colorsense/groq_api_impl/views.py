"""
Groq API Views
"""
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .service import groq_service
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def groq_chat(request):
    """Chat endpoint"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        model = data.get('model', None)
        
        if not message:
            return JsonResponse({"success": False, "error": "Message required"}, status=400)
        
        result = groq_service.simple_chat(message, model)
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_POST
def groq_vision(request):
    """Vision analysis endpoint"""
    try:
        text = request.POST.get('text', '').strip()
        model = request.POST.get('model', None)
        
        if 'image' not in request.FILES:
            return JsonResponse({"success": False, "error": "Image required"}, status=400)
        
        if not text:
            text = "Describe this image in detail"
        
        image_file = request.FILES['image']
        result = groq_service.vision_analysis(text, image_file, model)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_POST
def groq_paint_consultation(request):
    """Paint consultation endpoint"""
    try:
        room_description = request.POST.get('room_description', '').strip()
        
        if not room_description:
            return JsonResponse({"success": False, "error": "Room description required"}, status=400)
        
        image_file = request.FILES.get('image', None)
        result = groq_service.paint_consultation(room_description, image_file)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@require_GET
def groq_models(request):
    """Get available models"""
    try:
        models = groq_service.get_models()
        return JsonResponse({"success": True, "models": models})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def groq_demo(request):
    """Groq demo page"""
    return render(request, "groq_demo.html")