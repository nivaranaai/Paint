from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='colorsense_index'),
    path('upload/', views.upload, name='upload'),
    path('api/agent/', views.agent_api, name='colorsense_agent_api'),
    path('upload_images/', views.upload_images, name='upload_images'),
    path('api/agent/confirm/', views.confirm_suggestion, name='confirm_suggestion'),
    #path('review/', views.review_suggestion, name='review_suggestion'),
    # User review flow
]
