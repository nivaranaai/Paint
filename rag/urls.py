from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload, name='upload'),
    path('retrieve/', views.retrieve, name='retrieve'),
    path('generate/', views.generate, name='generate'),
]