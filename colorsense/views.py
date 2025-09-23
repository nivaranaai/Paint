from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .agent import run_agent, summrise_input, paint_suggestion
try:
    from .reconstruct import reconstruct_3d, pointcloud_to_textured_mesh
except ImportError:
    reconstruct_3d = None
    pointcloud_to_textured_mesh = None
from django.conf import settings
import os
import time
import pdb

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
        # Run the agent workflow
        result = summrise_input(user_text=message, image_uploads=images, doc_uploads=docs)
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
        images = []
        docs = []
        # Run the agent workflow
        result = run_agent(user_text=room_description, image_uploads=images, doc_uploads=docs)
        print(result)
        return JsonResponse({"ok": True, "message": "Suggestion confirmed.", "reply": result.get("reply", "")})
    else:
        return JsonResponse({"ok": False, "message": "Suggestion rejected."})



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
