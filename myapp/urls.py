from .views import * 
from django.urls import path

urlpatterns = [
    path('upload-profile-picture/', UserProfilePictureView.as_view(), name='profile-picture'),
    path('upload-document/', DocumentUploadView.as_view(), name='upload-document'),
    path('room-create/', RoomAPIView.as_view(), name='room-create'),
    path('room-image/', RoomImageAPIView.as_view(), name='room-image'),
    path('location/', LocationCreateAPIView.as_view(), name='location'),
    
]
