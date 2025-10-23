from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .agent import run_agent, summrise_input, paint_suggestion
from .interactive_painter import interactive_painter
from .enhanced_painter import enhanced_painter
import uuid
try:
    from .reconstruct import reconstruct_3d, pointcloud_to_textured_mesh
except ImportError:
    reconstruct_3d = None
    pointcloud_to_textured_mesh = None
from django.conf import settings
import os
import time
import pdb
import json
from django.views.decorators.csrf import csrf_exempt

@ensure_csrf_cookie
def index(request):
    """ColorSense upload page with Nivarana styling."""
    return render(request, "colorsense/colorsense_upload.html")

def nivarana_index(request):
    """Nivarana.ai landing page."""
    return render(request, "colorsense/nivarana_index.html")

def index_original(request):
    """Original chat UI."""
    return render(request, "colorsense/index.html")

def test_static(request):
    """Test static files."""
    return render(request, "colorsense/test_static.html")

@require_POST
def agent_api(request):
    """
    Accepts multipart/form-data with fields:
    - message: str
    - images: multiple image files
    - docs: multiple text files (.txt/.md)
    Returns JSON with 'reply' and 'swatches'.
    """
    message = request.POST.get("message", "").strip()
    images = request.FILES.getlist("images") or []
    docs = request.FILES.getlist("docs") or []
    provider = request.POST.get("provider", "groq")
    if not message and not images and not docs:
        return HttpResponseBadRequest("Please provide a message, image(s), or document(s).")

    try:
        # Run the agent workflow
        result = summrise_input(user_text=message, image_uploads=images, doc_uploads=docs, provider=provider)
        print(result)
        return JsonResponse({
            "ok": True,
            "reply": result.get("reply", ""),
            "swatches": result.get("swatches", []),
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@require_POST
def confirm_suggestion(request):
    """Handle user confirmation of the suggestion."""
    confirm = request.POST.get("confirm", "false").strip().lower()
    if confirm == "true":
        room_description = request.POST.get("room_description", "").strip()
        print(room_description)
        images = request.POST.getlist("images") or []
        docs = []
        # Run the agent workflow
        result = paint_suggestion(user_text=room_description, image_uploads=images, doc_uploads=docs)
        #result = parse_response(result['reply'])
        print(result)
        return JsonResponse({"ok": True, "message": "Suggestion confirmed.", "reply": result})
    else:
        return JsonResponse({"ok": False, "message": "Suggestion rejected."})


def parse_response(response):
    try:
        recomendation = json.loads(response)
        print(recomendation)
        #breakpoint()
        return recomendation
    except json.JSONDecodeError:
        return None

def upload(request):
    return render(request, "colorsense/upload.html")

def upload_images(request):
    if request.method == "POST":
        files = request.FILES.getlist("images")
        folder = os.path.join(settings.MEDIA_ROOT, "user_images")
        os.makedirs(folder, exist_ok=True)

        # Save images
        for f in files:
            img_path = os.path.join(folder, f.name)
            with open(img_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

        # Run reconstruction pipeline (if available)
        if reconstruct_3d and pointcloud_to_textured_mesh:
            ply_path = reconstruct_3d(folder)
            mesh_path = pointcloud_to_textured_mesh(ply_path)
        else:
            mesh_path = None

        # Return mesh URL or error
        if mesh_path:
            mesh_url = os.path.join(settings.MEDIA_URL, os.path.basename(mesh_path))
            return render(request, "viewer.html", {"mesh_url": mesh_url})
        else:
            return render(request, "upload.html", {"error": "3D reconstruction not available"})

    return render(request, "upload.html")

@require_POST
def create_paint_session(request):
    """Create interactive painting session"""
    try:
        image_data = request.POST.get('image_data')
        session_id = str(uuid.uuid4())
        
        if interactive_painter.create_session(image_data, session_id):
            return JsonResponse({
                'success': True,
                'session_id': session_id
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to create session'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def paint_at_point(request):
    """Paint at specific coordinates"""
    try:
        session_id = request.POST.get('session_id')
        x = int(request.POST.get('x'))
        y = int(request.POST.get('y'))
        color = request.POST.get('color')
        
        result = interactive_painter.paint_at_point(session_id, x, y, color)
        
        if result:
            return JsonResponse({
                'success': True,
                'image': result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to paint'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def reset_paint_session(request):
    """Reset painting session"""
    try:
        session_id = request.POST.get('session_id')
        result = interactive_painter.reset_session(session_id)
        
        if result:
            return JsonResponse({
                'success': True,
                'image': result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to reset'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_paint_session(request, session_id):
    """Get current painted image"""
    try:
        result = interactive_painter.get_current_image(session_id)
        
        if result:
            return JsonResponse({
                'success': True,
                'image': result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Session not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Enhanced Paint Studio Views
@csrf_exempt
@require_POST
def create_enhanced_session(request):
    """Create enhanced paint session with carousel and recommendations"""
    try:
        data = json.loads(request.body)
        images_data = data.get('images', [])
        paint_recommendations = data.get('recommendations', [])
        
        session_id = enhanced_painter.create_carousel_session(images_data, paint_recommendations)
        
        if session_id:
            result = enhanced_painter.get_current_image_data(session_id)
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                **result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to create session'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def switch_carousel_image(request):
    """Switch to next/previous image in carousel"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        direction = data.get('direction', 'next')
        
        result = enhanced_painter.switch_image(session_id, direction)
        
        if result:
            return JsonResponse({
                'success': True,
                **result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to switch image'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def preview_enhanced_segment(request):
    """Preview segment in enhanced studio"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        x = int(data.get('x'))
        y = int(data.get('y'))
        
        result = enhanced_painter.get_segment_preview(session_id, x, y)
        
        if result:
            return JsonResponse({
                'success': True,
                **result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Preview failed'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def apply_enhanced_color(request):
    """Apply recommended color to segment"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        x = int(data.get('x'))
        y = int(data.get('y'))
        color = data.get('color')
        blend_mode = data.get('blend_mode', 'normal')
        opacity = float(data.get('opacity', 0.7))
        
        result = enhanced_painter.apply_recommended_color(session_id, x, y, color, blend_mode, opacity)
        
        if result:
            return JsonResponse({
                'success': True,
                **result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Color application failed'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def reset_enhanced_image(request):
    """Reset current image in enhanced studio"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        result = enhanced_painter.reset_current_image(session_id)
        
        if result:
            return JsonResponse({
                'success': True,
                **result
            })
        else:
            return JsonResponse({'success': False, 'error': 'Reset failed'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def enhanced_studio_demo(request):
    """Render enhanced paint studio demo page"""
    return render(request, "colorsense/enhanced_paint_studio.html")
