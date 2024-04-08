from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user_instance = super().save(*args, **kwargs)
        user_instance.set_password(self.validated_data['password'])
        user_instance.save()
        return user_instance


class UserSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'address', 'phone', 'verification']


class OwnerSignUpSerializer(UserSerializer):

    def create(self, validated_data):
        user = super().create(validated_data)
        user.role, _ = Role.objects.get_or_create(name=Role.OWNER)
        user.save()
        return user


class TenantSignUpSerializer(UserSerializer):

    def create(self, validated_data):
        user = super().create(validated_data)
        user.role, _ = Role.objects.get_or_create(name=Role.TENANT)
        user.save()
        return user


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ['username', 'password']
