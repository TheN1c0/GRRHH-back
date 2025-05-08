from django.urls import path
from .views import RegisterView, LoginView, DashboardView, CookieTokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh_cookie'),
]
