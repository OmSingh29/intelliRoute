from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/analyze/', views.analyze_feedback, name='analyze_feedback'),
    path('dashboard/', views.dashboard, name='dashboard'),
]