from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Empleado, Cargo
from .serializers import EmpleadoSerializer, CargoSerializer

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

class CargoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]  # o AllowAny para que cualquiera pueda ver