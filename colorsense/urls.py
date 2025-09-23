from django.urls import path
from . import views
from .colorizer_opencv import views as colorizer_views

urlpatterns = [
    path('', views.index, name='colorsense_index'),
    path('upload/', views.upload, name='upload'),
    path('api/agent/', views.agent_api, name='colorsense_agent_api'),
    path('upload_images/', views.upload_images, name='upload_images'),
    path('api/agent/confirm/', views.confirm_suggestion, name='confirm_suggestion'),
    
    # Colorizer API endpoints
    path('api/colorizer/upload/', colorizer_views.upload_image_for_coloring, name='colorizer_upload'),
    path('api/colorizer/color/', colorizer_views.color_image_point, name='colorizer_color'),
    path('api/colorizer/reset/', colorizer_views.reset_image, name='colorizer_reset'),
    path('api/colorizer/save/', colorizer_views.save_colored_image, name='colorizer_save'),
    path('api/colorizer/session/<str:session_id>/', colorizer_views.get_session_image, name='colorizer_session'),
    path('api/colorizer/cleanup/', colorizer_views.cleanup_session, name='colorizer_cleanup'),
    path('colorizer/demo/', colorizer_views.colorizer_demo, name='colorizer_demo'),
]
