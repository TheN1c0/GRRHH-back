from django.urls import path
from .views import RegisterView, LoginView, DashboardView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
