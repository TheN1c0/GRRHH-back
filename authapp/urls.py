from django.urls import path
from .views import RegisterView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
]
