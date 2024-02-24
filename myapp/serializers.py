from rest_framework import serializers
from .models import *


class UserProfilePictureseriliazer(serializers.ModelSerializer):
    class Meta:
        model = UserProfilePicture
        fields = '__all__'


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentUpload
        fields = ['id', 'user', 'document_type', 'document_image']


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ['id', 'user', 'room_id', 'room_image']


class RoomSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='user.username', read_only=True)
    room_images = RoomImageSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'user', 'owner_name', 'room_type', 'no_of_room', 'bathroom_type', 'kitchen_slab',
                  'created_date', 'rent', 'available', 'wifi', 'water_type', 'room_images']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude', 'room']

    def create(self, validated_data):
        return Location.objects.create(**validated_data)


class RentedRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentedRoom
        fields = "__all__"
