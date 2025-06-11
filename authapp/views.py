from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, NotaSerializer
import json
from .models import HistorialAcceso
from rest_framework.decorators import api_view, permission_classes
from .models import Nota


class RegisterView(APIView):
    def get(self, request, *args, **kwargs):
        # Respuesta de prueba para confirmar que la URL está funcionando
        return Response(
            {"message": "El endpoint de registro está activo"},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Usuario creado'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)"""
        if request.method == "POST":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "JSON inválido"}, status=400)

            # Imprime en consola para verificar los datos recibidos
            print("Datos recibidos:", data)

            return JsonResponse(
                {"message": "Datos recibidos correctamente", "data": data}, status=200
            )
        else:
            return JsonResponse({"error": "Solo se permite el método POST"}, status=405)


from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from .auth_backend import CookieJWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

User = get_user_model()
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    authentication_classes = []  # 👈 Este cambio es clave
    permission_classes = [AllowAny]  # Permitir acceso libre

    def post(self, request):
        user_input = request.data.get("username")  # puede ser email o username
        password = request.data.get("password")
        logger.info(f"Usuario recibido: {user_input}")
        logger.info(f"Contraseña recibida: {password}")
        # Buscar por email si es un correo
        if "@" in user_input:
            try:
                user_obj = User.objects.get(email=user_input)
                username = user_obj.username
            except User.DoesNotExist:
                return Response(
                    {"detail": "Email no registrado"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            username = user_input

        user = authenticate(request, username=username, password=password)

        if user:
            registrar_acceso(request, user)
            refresh = RefreshToken.for_user(user)
            response = Response(
                {"refresh": str(refresh), "username": user.username},
                status=status.HTTP_200_OK,
            )
            response.set_cookie(
                key="access_token",
                value=str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
            )

            # 🔐 Guardar refresh_token como cookie también
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=False,  # Cambiar a True en producción
                samesite="Lax",
                path="/auth/api/refresh/",
            )

            return response
        else:
            response = Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response.delete_cookie("access_token")

            return response


class DashboardView(APIView):
    authentication_classes = [
        CookieJWTAuthentication
    ]  # se llama por defecto, no la invocamos
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "message": f"Bienvenido {request.user.username}",
                "usuario_id": request.user.id,
            }
        )


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found in cookies"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get("access")

        # Creamos la respuesta
        response = Response({"access": access_token}, status=status.HTTP_200_OK)

        # ✅ Actualizamos la cookie del access_token
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # cambia a True en producción
            samesite="Lax",
            path="/",
        )

        return response


def registrar_acceso(request, usuario):
    ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    HistorialAcceso.objects.create(usuario=usuario, ip=ip, user_agent=user_agent)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ultimo_acceso(request):
    accesos = HistorialAcceso.objects.filter(usuario=request.user).order_by("-fecha")[
        :3
    ]  # 👈 obtenemos los 3 últimos accesos

    if not accesos:
        return Response({"error": "No hay accesos registrados"}, status=404)

    data = [
        {
            "ip": acc.ip,
            "fecha": acc.fecha.strftime("%Y-%m-%d %H:%M"),
            "user_agent": acc.user_agent[:120],
        }
        for acc in accesos
    ]

    return Response(data)


@api_view(["GET", "POST", "DELETE", "PUT"])
@permission_classes([IsAuthenticated])
def notas_usuario(request):
    user = request.user

    if request.method == "GET":
        notas = Nota.objects.filter(usuario=user).order_by("-fecha_creacion")[:5]
        serializer = NotaSerializer(notas, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        serializer = NotaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(usuario=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    if request.method == "DELETE":
        nota_id = request.data.get("id")
        try:
            nota = Nota.objects.get(id=nota_id, usuario=user)
            nota.delete()
            return Response({"success": True})
        except Nota.DoesNotExist:
            return Response({"error": "Nota no encontrada"}, status=404)

    if request.method == "PUT":
        nota_id = request.data.get("id")
        try:
            nota = Nota.objects.get(id=nota_id, usuario=user)
            serializer = NotaSerializer(nota, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except Nota.DoesNotExist:
            return Response({"error": "Nota no encontrada"}, status=404)
