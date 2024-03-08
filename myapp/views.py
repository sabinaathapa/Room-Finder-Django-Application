from datetime import timezone
from uuid import UUID
from django.core.serializers import serialize
from rest_framework import generics, permissions, response, status
from django.shortcuts import get_object_or_404
import requests
from django.http import JsonResponse
from django.db.models import Prefetch
from .rabbitmq_utils import RabbitMQProducer
from rest_framework.generics import ListCreateAPIView
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response


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

    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        room_serializer = self.get_serializer(data=request.data)
        room_serializer.is_valid(raise_exception=True)
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

    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room_id = self.request.data.get('room')
        serializer.save(user=self.request.user, room_id=room_id)


def hitting_external_api(id):
    external_api_url = 'http://localhost:8089/api/v1/spatial-data/insert-into-quad-tree'
    try:
        headers = {
            "Request-Key": "abc123"
        }
        params = {'id': id}
        response = requests.get(external_api_url, headers=headers, params=params)
        if response.status_code == 200:
            print("Request was Successful")
        else:
            print("Request was not Successful")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("Request was not Successful")


class LocationCreateAPIView(generics.ListCreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        room_id = self.request.data.get('room')
        room = get_object_or_404(Room, id=room_id)
        location = serializer.save(room=room)
        hitting_external_api(location.id)


class RentedRoomCreate(generics.CreateAPIView):
    queryset = RentedRoom.objects.all()
    serializer_class = RentedRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.validated_data['tenant_id'] = self.request.user
        room_id = self.request.data.get('room_id')
        room = Room.objects.get(id=room_id)
        serializer.validated_data['owner_id'] = room.user
        # serializer.validated_data['booking_date'] = timezone.now()
        serializer.save()


class SearchAPIView(APIView):
    def get(self, request):
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        search_radius = self.request.query_params.get('search_radius')
        if lat and lon and search_radius is None:
            return Response("Latitude, Longitude and Search radius is required.")

        external_api_url = "http://localhost:8089/api/v1/spatial-data/get-nearest-rooms"
        try:
            headers = {"Request-Key": "abc123"}
            params = {'lat': lat, 'long': lon, 'searchRadiusInKm': search_radius}
            response = requests.get(external_api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                uuids = [item['uuid'] for item in data]

                # Convert UUID strings to UUID objects
                uuid_objects = [UUID(uuid_str) for uuid_str in uuids]

                # Query the database for records with these UUIDs
                return_data = []
                for uuid_object in uuid_objects:
                    location_with_room = Location.objects.filter(id=uuid_object).prefetch_related(
                        'room__room_images').first()
                    serialized_data = {
                        'location': serialize('json', [location_with_room], use_natural_foreign_keys=True),
                        'room': serialize('json', [location_with_room.room], use_natural_foreign_keys=True),
                        'image': serialize('json', location_with_room.room.room_images.all())
                    }
                    return_data.append(serialized_data)
                return JsonResponse(return_data, safe=False)
                # return Response(return_data)
            else:
                request_fail = "Request was not successful."
                print(request_fail)
                return Response(request_fail, status=500)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            failure_message = "Request was not Successful"
            print(failure_message)
            return Response(failure_message, status=500)


#################### OWNER"S ####################
# Get the rooms Created By that Owner.
class GetOwnerCreatedRoomAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        userId = request.user.id

        allRooms = Room.objects.filter(user_id=userId).prefetch_related()
        print(allRooms)
        # Convert queryset to a list of dictionaries
        rooms_list = []
        for room in allRooms:
            print(room)
            image_link = RoomImage.objects.filter(room_id=room.id).get()
            roomLocation = Location.objects.filter(room_id=room.id).get()

            rooms_list.append(
                {'id': room.id, 'roomType': room.room_type,
                 'noOfRooms': room.no_of_room, 'user_id': room.user_id,
                 'bathroomType': room.bathroom_type, 'kitchenSlab': room.kitchen_slab,
                 'wifi': room.wifi, 'waterType': room.water_type,
                 'imageLink': str(image_link.room_image),
                 'coordinates': str(roomLocation.latitude) + ", " + str(roomLocation.longitude),
                 'locationName': roomLocation.name
                 }
            )

        # Return the JsonResponse with a dictionary containing the list
        return JsonResponse({'rooms': rooms_list}, safe=False)


# Get the rooms booked for that owner
class GetBookingRequestRoomAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Extracting data from params
        userId = request.user.id
        status = request.query_params.get('status')

        allRooms = RentedRoom.objects.filter(owner_id_id=userId, status=status)

        # Preparing the Data for return
        returnData = []
        for room in allRooms:
            roomDetails = Room.objects.get(id=room.room_id_id)
            imageLink = RoomImage.objects.filter(room_id=room.room_id_id).get()
            tenantDetails = User.objects.filter(id=room.tenant_id_id).get()
            roomLocation = Location.objects.filter(room_id=room.room_id_id).get()

            returnData.append(
                {'roomId': roomDetails.id,
                 'bookingTableId': room.id,
                 'roomType': roomDetails.room_type,
                 'noOfRooms': roomDetails.no_of_room,
                 'bathroomType': roomDetails.bathroom_type,
                 'kitchenSlab': roomDetails.kitchen_slab,
                 'wifi': roomDetails.wifi,
                 'waterType': roomDetails.water_type,
                 'imageLink': str(imageLink.room_image),
                 'latitude': roomLocation.latitude,
                 'longitude': roomLocation.longitude,
                 'locationName': roomLocation.name,
                 'tenantEmail': tenantDetails.email,
                 'tenantPhone': tenantDetails.phone,
                 'tenantName': tenantDetails.first_name + " " + tenantDetails.last_name,
                 'tenantAddress': tenantDetails.address,
                 'status': room.status
                 }
            )

        return JsonResponse(returnData, safe=False)


#Accept the Booking Request
class AcceptBookingRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookingTableId = request.query_params.get('roomBookId')


        try:

            roomBookingDetails = RentedRoom.objects.get(id=bookingTableId)
            roomDetails = Room.objects.filter(id=roomBookingDetails.room_id_id).get()
            locationDetails = Location.objects.filter(room_id=roomDetails.id).get()

        except RentedRoom.DoesNotExist:
            return JsonResponse({"error": "Room booking not found"}, status=404)

        roomBookingDetails.status = "ACCEPTED"
        roomBookingDetails.save(update_fields=['status'])

        roomDetails.available = "False"
        roomDetails.save(update_fields=['available'])

        tenant_user = roomBookingDetails.tenant_id
        rabbit_producer = RabbitMQProducer(
            rabbitmq_host='192.168.56.156',
            rabbitmq_port=5672,
            exchange_name='rabbitmq_exchange',
            queue_name='booking_queue',
            binding_key='rabbitmq_binding_key'
        )
        json_data = {
            "owner":{
                "name": request.user.username,
                "email": request.user.email,
                "phone": request.user.phone,
                "address": request.user.address
            },
            "room": {
                "location": locationDetails.name,
                "rent":  str(roomDetails.rent),
                "bathroomType": roomDetails.bathroom_type,
                "kitchenSlab": "Yes" if roomDetails.kitchen_slab else "No"
            },
            "tenant": {
                "name":  tenant_user.username,
                "email": tenant_user.email,
                "phone": tenant_user.phone,
                "address": tenant_user.address
            }
        }
        rabbit_producer.send_message(json_data, routing_key='rabbitmq_binding_key', exchange='rabbitmq_exchange')
        rabbit_producer.close_connection()


        return JsonResponse("Room Booking Accepted", safe=False)



class RejectBookingRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookingTableId = request.query_params.get('roomBookId')

        try:
            roomBookingDetails = RentedRoom.objects.get(id=bookingTableId)
        except RentedRoom.DoesNotExist:
            return JsonResponse({"error": "Room booking not found"}, status=404)

        roomBookingDetails.status = "REJECTED"
        roomBookingDetails.save(update_fields=['status'])

        return JsonResponse("Room Booking Rejected", safe=False)



