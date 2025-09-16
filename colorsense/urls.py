from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='colorsense_index'),
    path('upload/', views.upload, name='upload'),
    path('api/agent/', views.agent_api, name='colorsense_agent_api'),
    path('upload_images/', views.upload_images, name='upload_images'),
    
    # User review flow
    path('review/<str:suggestion_id>/', views.review_suggestion, name='review_suggestion'),
    path('api/suggestions/<str:suggestion_id>/', views.get_suggestion_status, name='suggestion_status'),
]
