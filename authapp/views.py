from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
import json
class RegisterView(APIView):
    def get(self, request, *args, **kwargs):
        # Respuesta de prueba para confirmar que la URL está funcionando
        return Response({"message": "El endpoint de registro está activo"}, status=status.HTTP_200_OK)
    
    
    def post(self, request):
        """ serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Usuario creado'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) """
        if request.method == "POST":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "JSON inválido"}, status=400)
            
            # Imprime en consola para verificar los datos recibidos
            print("Datos recibidos:", data)
        
            return JsonResponse({"message": "Datos recibidos correctamente", "data": data}, status=200)
        else:
            return JsonResponse({"error": "Solo se permite el método POST"}, status=405)
        
    
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated,AllowAny
from .auth_backend import CookieJWTAuthentication
User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        user_input = request.data.get('username')  # puede ser email o username
        password = request.data.get('password')

        # Buscar por email si es un correo
        if '@' in user_input:
            try:
                user_obj = User.objects.get(email=user_input)
                username = user_obj.username
            except User.DoesNotExist:
                return Response({'detail': 'Email no registrado'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            username = user_input

        user = authenticate(request, username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            response = Response({'refresh': str(refresh)}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/'
            )
            return response
        else:
            response = Response({'detail': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie('access_token')  # 💥 Aquí se borra si ya había una
            return response





class DashboardView(APIView):
    authentication_classes = [CookieJWTAuthentication]#se llama por defecto, no la invocamos
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'message': f'Bienvenido {request.user.username}',
            'usuario_id': request.user.id
        })
