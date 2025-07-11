from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    DashboardView,
    CookieTokenRefreshView,
    ultimo_acceso,
    notas_usuario,
    LogoutView,
    mi_cuenta,
    reenviar_verificacion_correo, 
    reenviar_verificacion_telefono,
    confirmar_verificacion_correo,
    confirmar_verificacion_telefono,
    UsuarioRRHHViewSet
)


router = DefaultRouter()
router.register(r'usuarios-rrhh', UsuarioRRHHViewSet, basename='usuarios-rrhh')



urlpatterns = [
    path('', include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("api/login/", LoginView.as_view(), name="login"),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh_cookie"),
    path("api/ultimo-acceso/", ultimo_acceso),
    path("api/notas/", notas_usuario),
    path("mi-cuenta/", mi_cuenta),
    path("mi-cuenta/verificar-correo/", reenviar_verificacion_correo),
    path("mi-cuenta/verificar-telefono/", reenviar_verificacion_telefono),
    path("mi-cuenta/verificar-email/", confirmar_verificacion_correo),
    path("mi-cuenta/confirmar-telefono/", confirmar_verificacion_telefono),
]
