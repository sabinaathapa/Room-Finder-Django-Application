from .views import * 
from django.urls import path

urlpatterns = [
    path('upload-profile-picture/', UserProfilePictureView.as_view(), name='profile-picture'),
    path('upload-document/', DocumentUploadView.as_view(), name='upload-document'),
    path('room-create/', RoomAPIView.as_view(), name='room-create'),
    path('room-image/', RoomImageAPIView.as_view(), name='room-image'),
    path('location/', LocationCreateAPIView.as_view(), name='location'),
    path('search_location/', SearchAPIView.as_view(), name='search-location'),
    path('get-created-room/', GetOwnerCreatedRoomAPIView.as_view(), name='get-owner-created-room'),
    path('rented-room/', RentedRoomCreate.as_view(), name='rented-room'),
    path('get-booking-request/',GetBookingRequestRoomAPIView.as_view(), name='get-booking-request'),
    path('accept-booking-request/', AcceptBookingRequestView.as_view(), name='accept-booking-request'),
    path('reject-booking-request/', RejectBookingRequestView.as_view(), name='reject-booking-request'),
    path('get-user-details/', GetUserdetailsView.as_view(), name='user-details'),
    path('room-details/', RoomDetailsAPIView.as_view(), name='room-details'),
    path('get-user-requested-room/', GetUserRequestedRoom.as_view(), name='get-user-requested-room'),
    path('cancel-booking-request/',CancelBookingRequest.as_view(), name='cancel-booking-request' ),
    path('get-available-room-location/',GetAvailableRoomLocation.as_view(), name='get-available-room-location'),
]

