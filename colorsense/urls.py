from django.urls import path
from . import views
from .colorizer_opencv import views as colorizer_views
from .groq_api_impl import views as groq_views
from .sam_studio import views as sam_studio_views

urlpatterns = [
    path('', views.nivarana_index, name='colorsense_index'),
    path('colorsense/', views.index, name='colorsense_app'),
    path('original/', views.index_original, name='index_original'),
    path('test-static/', views.test_static, name='test_static'),
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
    
    # Groq API endpoints
    path('api/groq/chat/', groq_views.groq_chat, name='groq_chat'),
    path('api/groq/vision/', groq_views.groq_vision, name='groq_vision'),
    path('api/groq/paint/', groq_views.groq_paint_consultation, name='groq_paint'),
    path('api/groq/models/', groq_views.groq_models, name='groq_models'),
    path('groq/demo/', groq_views.groq_demo, name='groq_demo'),
    
    # Interactive painting endpoints
    path('api/paint/create/', views.create_paint_session, name='create_paint_session'),
    path('api/paint/point/', views.paint_at_point, name='paint_at_point'),
    path('api/paint/reset/', views.reset_paint_session, name='reset_paint_session'),
    path('api/paint/session/<str:session_id>/', views.get_paint_session, name='get_paint_session'),
    
    # SAM Studio API
    path('api/sam-studio/create/', sam_studio_views.create_studio_session, name='sam_studio_create'),
    path('api/sam-studio/apply-color/', sam_studio_views.apply_color, name='sam_studio_apply'),
    
    # SAM Studio
    path('sam-studio/', sam_studio_views.sam_studio_demo, name='sam_studio_demo'),
]
