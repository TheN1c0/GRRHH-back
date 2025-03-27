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
