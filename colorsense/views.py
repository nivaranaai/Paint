from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .agent import run_agent, summrise_input, paint_suggestion, extract_hex_codes
from .interactive_painter import interactive_painter
import uuid
from .interactive_painter import interactive_painter
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
@csrf_exempt
@require_POST
def gemini_color_recommendations(request):
    """API endpoint for color recommendations using Gemini."""
    try:
        from rag.Vector import generate_answer_with_gemini
        
        data = json.loads(request.body)
        room_description = data.get('room_description', '')
        style_preferences = data.get('style_preferences', '')
        
        if not room_description:
            return JsonResponse({'error': 'Room description is required'}, status=400)
        
        query = f"Recommend paint colors for: {room_description}. Style preferences: {style_preferences}"
        context = "Provide 3-5 paint color recommendations with HEX codes, finishes, and rationales."
        
        answer = generate_answer_with_gemini(query, context)
        swatches = extract_hex_codes(answer)
        
        return JsonResponse({
            'recommendations': answer,
            'swatches': swatches
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
@require_POST
def upsert_pdf_api(request):
    """API endpoint for upsert_pdf_to_pinecone method."""
    try:
        from rag.Vector import upsert_pdf_to_pinecone, differentiators
        
        data = json.loads(request.body)
        pdf_path = data.get('pdf_path', '')
        
        if not pdf_path:
            return JsonResponse({'error': 'pdf_path is required'}, status=400)
        
        upsert_pdf_to_pinecone(pdf_path, differentiators)
        return JsonResponse({'message': 'PDF processed and upserted to Pinecone successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)