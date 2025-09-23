"""
Django views for image colorization API
"""
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .service import colorizer_service
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def upload_image_for_coloring(request):
    """
    Upload image and create colorizer session
    POST /api/colorizer/upload/
    Form data: image file
    Returns: session_id and base64 image
    """
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                "success": False, 
                "error": "No image file provided"
            }, status=400)
        
        image_file = request.FILES['image']
        result = colorizer_service.create_session(image_file)
        
        if result["success"]:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"Error in upload_image_for_coloring: {e}")
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)

@csrf_exempt
@require_POST
def color_image_point(request):
    """
    Color image at specified point
    POST /api/colorizer/color/
    JSON: {session_id, x, y, color}
    Returns: updated base64 image
    """
    try:
        data = json.loads(request.body)
        
        required_fields = ['session_id', 'x', 'y', 'color']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    "success": False, 
                    "error": f"Missing required field: {field}"
                }, status=400)
        
        result = colorizer_service.color_at_point(
            session_id=data['session_id'],
            x=int(data['x']),
            y=int(data['y']),
            color=data['color']
        )
        
        if result["success"]:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "error": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in color_image_point: {e}")
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)

@csrf_exempt
@require_POST
def reset_image(request):
    """
    Reset image to original state
    POST /api/colorizer/reset/
    JSON: {session_id}
    Returns: original base64 image
    """
    try:
        data = json.loads(request.body)
        
        if 'session_id' not in data:
            return JsonResponse({
                "success": False, 
                "error": "Missing session_id"
            }, status=400)
        
        result = colorizer_service.reset_session(data['session_id'])
        
        if result["success"]:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "error": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in reset_image: {e}")
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)

@csrf_exempt
@require_POST
def save_colored_image(request):
    """
    Save current colored image
    POST /api/colorizer/save/
    JSON: {session_id, filename (optional)}
    Returns: file URL
    """
    try:
        data = json.loads(request.body)
        
        if 'session_id' not in data:
            return JsonResponse({
                "success": False, 
                "error": "Missing session_id"
            }, status=400)
        
        filename = data.get('filename', None)
        result = colorizer_service.save_session_image(
            session_id=data['session_id'],
            filename=filename
        )
        
        if result["success"]:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "error": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in save_colored_image: {e}")
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)

@require_GET
def get_session_image(request, session_id):
    """
    Get current session image
    GET /api/colorizer/session/{session_id}/
    Returns: current base64 image
    """
    try:
        result = colorizer_service.get_session_image(session_id)
        
        if result["success"]:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=404)
            
    except Exception as e:
        logger.error(f"Error in get_session_image: {e}")
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)

@csrf_exempt
@require_POST
def cleanup_session(request):
    """
    Clean up session resources
    POST /api/colorizer/cleanup/
    JSON: {session_id}
    Returns: success status
    """
    try:
        data = json.loads(request.body)
        
        if 'session_id' not in data:
            return JsonResponse({
                "success": False, 
                "error": "Missing session_id"
            }, status=400)
        
        success = colorizer_service.cleanup_session(data['session_id'])
        return JsonResponse({"success": success})
            
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "error": "Invalid JSON data"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in cleanup_session: {e}")
        return JsonResponse({
            "success": False, 
            "error": str(e)
        }, status=500)

def colorizer_demo(request):
    """Render colorizer demo page"""
    return render(request, "colorizer_demo.html")