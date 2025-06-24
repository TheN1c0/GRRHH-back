from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, NotaSerializer, MiCuentaSerializer, PerfilUsuarioSerializer
import json
from .models import HistorialAcceso,  PerfilUsuario, Nota
from rest_framework.decorators import api_view, permission_classes
from django.core.signing import TimestampSigner
from django.conf import settings
from pathlib import Path
from dotenv import load_dotenv




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

from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from .auth_backend import CookieJWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.core.mail import send_mail
User = get_user_model()
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    authentication_classes = []  
    permission_classes = [AllowAny]  

    def post(self, request):
        user_input = request.data.get("username")  
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
                secure=True,
                samesite="None",
                path="/",
            )

            # 🔐 Guardar refresh_token como cookie también
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=True,  # Cambiar a True en producción
                samesite="None",
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

class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)

        # Eliminar cookies
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/auth/api/refresh/")

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
            secure=True,  # cambia a True en producción
            samesite="None",
            path="/",
        )

        return response


def registrar_acceso(request, usuario):
    # Obtener IP y corregir múltiples IPs separadas por coma
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    if "," in ip:
        ip = ip.split(",")[0].strip()

    user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    HistorialAcceso.objects.create(
        usuario=usuario,
        ip=ip,
        user_agent=user_agent,
    )



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

@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def mi_cuenta(request):
    usuario = request.user

    if request.method == "GET":
        serializer = MiCuentaSerializer(usuario)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = MiCuentaSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reenviar_verificacion_correo(request):
    from django.core.signing import TimestampSigner

    user = request.user
    perfil, creado = PerfilUsuario.objects.get_or_create(user=user)

    if not perfil.nuevo_email:
        return Response({"detail": "No hay un correo pendiente de verificación."}, status=400)

    signer = TimestampSigner()
    token = signer.sign(user.id)
    frontend_url = settings.FRONTEND_URL
    url = f"{frontend_url}/verificar-email?token={token}"

    send_mail(
        subject="Verifica tu nuevo correo",
        message=f"Hola {user.first_name}, verifica tu correo aquí: {url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[perfil.nuevo_email],
        html_message=f"""
            <p>Hola {user.first_name},</p>
            <p>Haz clic en el siguiente enlace para verificar tu correo:</p>
            <p><a href="{url}" target="_blank">{url}</a></p>
            <p>Si no solicitaste este cambio, puedes ignorar este mensaje.</p>
        """,
    )

    return Response({"detail": "Correo de verificación enviado."})


@api_view(["GET"])
@permission_classes([]) 
def confirmar_verificacion_correo(request):
    token = request.query_params.get("token")

    if not token:
        return Response({"detail": "Token faltante."}, status=400)

    signer = TimestampSigner()
    try:
        user_id = signer.unsign(token, max_age=86400)  # 24 horas
    except SignatureExpired:
        return Response({"detail": "El enlace ha expirado."}, status=400)
    except BadSignature:
        return Response({"detail": "Enlace inválido."}, status=400)

    try:
        user = User.objects.get(id=user_id)
        perfil = user.perfil

        if not perfil.nuevo_email:
            return Response({"detail": "No hay un correo pendiente de confirmación."}, status=400)

        # Confirmar correo
        user.email = perfil.nuevo_email
        perfil.email_verificado = True
        perfil.nuevo_email = ''
        user.save()
        perfil.save()

        return Response({"detail": "Correo verificado exitosamente."})

    except User.DoesNotExist:
        return Response({"detail": "Usuario no encontrado."}, status=404)

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reenviar_verificacion_telefono(request):
    user = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)

    if not perfil.nuevo_telefono:
        return Response({"detail": "No hay un número pendiente de verificación."}, status=400)

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalSMSApi(sib_api_v3_sdk.ApiClient(configuration))

    codigo = perfil.generate_sms_code()  # esta función debe existir en tu modelo
    sms_req = sib_api_v3_sdk.SendTransacSms(
        sender="MyCompany",
        recipient=perfil.nuevo_telefono,
        content=f"Tu código de verificación es: {codigo}"
    )

    try:
        api_instance.send_transac_sms(sms_req)
        return Response({"detail": "Mensaje SMS enviado correctamente."})
    except ApiException as e:
        return Response({"detail": "Error al enviar SMS.", "error": str(e)}, status=500)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirmar_verificacion_telefono(request):
    codigo = request.data.get("code")

    if not codigo:
        return Response({"detail": "Código faltante."}, status=400)

    perfil = request.user.perfil

    if perfil.verify_sms_code(codigo):
        return Response({"detail": "📱 Teléfono verificado correctamente."})

    return Response({"detail": "❌ Código inválido o expirado."}, status=400)


# views.py

from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import UsuarioRRHHSerializer, PermisosRRHHSerializer
from .models import PerfilUsuario, PermisosRRHH
from rest_framework.permissions import IsAuthenticated
from django.db import transaction


class UsuarioRRHHViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsuarioRRHHSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data

        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                is_superuser=data.get("is_superuser", False),
                is_staff=True
            )

            PerfilUsuario.objects.create(user=user)

            PermisosRRHH.objects.create(
                user=user,
                solo_lectura=data.get("solo_lectura", False),
                puede_eliminar=data.get("puede_eliminar", False),
            )

        return Response({"mensaje": "Usuario creado exitosamente"}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data

        with transaction.atomic():
            user.email = data.get("email", user.email)
            user.is_superuser = data.get("is_superuser", user.is_superuser)
            user.save()

            # Actualiza permisos
            permisos, _ = PermisosRRHH.objects.get_or_create(user=user)
            permisos.solo_lectura = data.get("solo_lectura", permisos.solo_lectura)
            permisos.puede_eliminar = data.get("puede_eliminar", permisos.puede_eliminar)
            permisos.save()

        return Response({"mensaje": "Usuario actualizado correctamente"})

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response({"mensaje": "Usuario eliminado"})
