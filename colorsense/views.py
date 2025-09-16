from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .agent import run_agent
from .reconstruct import reconstruct_3d, pointcloud_to_textured_mesh
from django.conf import settings
import os
import time

@ensure_csrf_cookie
def index(request):
    """Render the chat UI."""
    return render(request, "colorsense/index.html")

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

    if not message and not images and not docs:
        return HttpResponseBadRequest("Please provide a message, image(s), or document(s).")

    try:
        result = run_agent(user_text=message, image_uploads=images, doc_uploads=docs)
        
        return JsonResponse({
            "ok": True,
            "reply": result.get("reply", ""),
            "swatches": result.get("swatches", []),
        })
        
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)































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

        # Run reconstruction pipeline
        ply_path = reconstruct_3d(folder)
        mesh_path = pointcloud_to_textured_mesh(ply_path)

        # Return mesh URL
        mesh_url = os.path.join(settings.MEDIA_URL, os.path.basename(mesh_path))
        return render(request, "viewer.html", {"mesh_url": mesh_url})

    return render(request, "upload.html")

























def review_suggestion(request):
    """Show a suggestion for user review"""
    suggestion = suggestions_store.get(suggestion_id)
    if not suggestion:
        return HttpResponseBadRequest("Suggestion not found or expired")
        
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            suggestion.status = "accepted"
            return JsonResponse({"status": "accepted"})
        elif action == "reject":
            suggestion.status = "rejected"
            return JsonResponse({"status": "rejected"})
    
    return render(request, "colorsense/review.html", {"suggestion": suggestion})

def get_suggestion_status(request, suggestion_id):
    """Get the current status of a suggestion"""
    suggestion = suggestions_store.get(suggestion_id)
    if not suggestion:
        return JsonResponse({"error": "Not found"}, status=404)
        
    return JsonResponse({
        "status": suggestion.status,
        "reply": suggestion.reply,
        "swatches": suggestion.swatches
    })
