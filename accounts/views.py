from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse


class OwnerSignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = OwnerSignUpSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'message': 'Owner signed up successfully'}, status=status.HTTP_201_CREATED, headers=headers)


class TenantSignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = TenantSignUpSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'message': 'Tenant signed up successfully'}, status=status.HTTP_201_CREATED, headers=headers)


class LoginAPIView(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            usersRole = Role.objects.get(id=user.role_id)

            response_data = {
                "status": status.HTTP_200_OK,
                "message": "success",
                "data": {
                    "access_token": access_token,
                    "refresh_token": str(refresh),
                    "userRole": usersRole.name
                },

            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "Invalid username or password",
            }
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


class Getuserroleview(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user_role = request.user.role.name if request.user.role else None
        return JsonResponse({'role': user_role})