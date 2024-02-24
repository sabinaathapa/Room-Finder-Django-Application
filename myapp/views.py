from rest_framework import generics, permissions, response, status

from .models import *
from .serializers import *


class UserProfilePictureView(generics.CreateAPIView):
    queryset = UserProfilePicture.objects.all()
    serializer_class = UserProfilePictureseriliazer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentUploadView(generics.CreateAPIView):
    queryset = DocumentUpload.objects.all()
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RoomAPIView(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        room_serializer = self.get_serializer(data=request.data)
        # print(request.data)
        room_serializer.is_valid(raise_exception=True)

        # room_id = request.data.get('room_id')
        self.perform_create(room_serializer)

        # Get the created room instance
        room_instance = room_serializer.instance

        uploaded_images = request.FILES.getlist('uploaded_images')
        for image in uploaded_images:
            RoomImage.objects.create(user=self.request.user, room=room_instance, room_image=image)

        headers = self.get_success_headers(room_serializer.data)
        return response.Response(room_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RoomImageAPIView(generics.ListCreateAPIView):
    queryset = RoomImage.objects.all()
    serializer_class = RoomImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room_id = self.request.data.get('room')
        serializer.save(user=self.request.user, room_id=room_id)


class LocationCreateAPIView(generics.CreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room_id = self.request.data.get('room_id')
        serializer.save(room=room_id)


class RentedRoomImageAPIView(generics.ListCreateAPIView):
    queryset = RentedRoom.objects.all()
    serializer_class = RentedRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room_id = self.request.data.get('room_id')
# TODO: Complete View and add urls
