from uuid import UUID
from rest_framework import generics, permissions, response, status
from django.shortcuts import get_object_or_404
import requests
from django.http import JsonResponse
from .rabbitmq_utils import RabbitMQProducer
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response


class UserProfilePictureView(generics.CreateAPIView):
    queryset = UserProfilePicture.objects.all()
    serializer_class = UserProfilePictureseriliazer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        uploaded_images = self.request.FILES.getlist('uploaded_images')

        # Check if the user already has a profile picture
        try:
            userProfile = UserProfilePicture.objects.get(user=self.request.user)
            # If the user has a profile picture, update it
            userProfile.profile_picture = uploaded_images
            serializer.instance = userProfile
            serializer.save()
        except UserProfilePicture.DoesNotExist:
            # If the user doesn't have a profile picture, create a new one
            serializer.save(user=self.request.user)


class DocumentUploadView(generics.CreateAPIView):
    queryset = DocumentUpload.objects.all()
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document_type = self.request.data.get('document_type')
        document_image = self.request.FILES.get('document_image')

        rabbit_producer = RabbitMQProducer(
            rabbitmq_host='192.168.56.156',
            rabbitmq_port=5672,
            exchange_name='rabbitmq_exchange',
            queue_name='document_alert',
            binding_key='document_alert_key'
        )

        try:
            # Try to get the DocumentUpload object for the current user and document_type
            user_docs = DocumentUpload.objects.filter(user=self.request.user, document_type=document_type).first()
            # If the user has an existing DocumentUpload object, update it
            if user_docs:
                user_docs.document_image = document_image
                user_docs.verification_status = DocumentUpload.VerificationStatus.PENDING
                user_docs.save()
                serializer.instance = user_docs
            else:
                # If the DocumentUpload object does not exist for the user, create a new one
                serializer.save(user=self.request.user, document_type=document_type, document_image=document_image)

            json_data = {
                'username': self.request.user.first_name + ' ' + self.request.user.last_name,
                'email': 'beeplaw21@gmail.com'
            }

            rabbit_producer.send_message(json_data, routing_key='document_alert_key', exchange='rabbitmq_exchange')
            rabbit_producer.close_connection()

        except Exception as e:
            # Handle any other exceptions that may occur
            print(f"Error: {e}")
            raise

class RoomAPIView(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

        # Get the created room instance
        room_instance = serializer.instance

        uploaded_images = self.request.FILES.getlist('uploaded_images')
        print('"Images:  ', uploaded_images)

    def create(self, request, *args, **kwargs):
        room_serializer = self.get_serializer(data=request.data)
        room_serializer.is_valid(raise_exception=True)
        self.perform_create(room_serializer)

        headers = self.get_success_headers(room_serializer.data)
        return response.Response(room_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class RoomImageAPIView(generics.ListCreateAPIView):
    queryset = RoomImage.objects.all()
    serializer_class = RoomImageSerializer

    # permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        print("Saving Room Image")
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


class RentedRoomCreate(generics.ListCreateAPIView):
    queryset = RentedRoom.objects.all()
    serializer_class = RentedRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        savedData = serializer.save(tenant_id=self.request.user)

        rabbit_producer = RabbitMQProducer(
            rabbitmq_host='192.168.56.156',
            rabbitmq_port=5672,
            exchange_name='rabbitmq_exchange',
            queue_name='booking_alert',
            binding_key='booking_alert_key'
        )

        json_data = {
            'ownerName': User.objects.get(id=savedData.tenant_id_id).first_name,
            'roomLocation':Location.objects.get(room_id=savedData.room_id_id).name,
            'tenant':self.request.user.first_name + ' '+ self.request.user.last_name,
            'expectedDate':str(savedData.rented_date),
            'offeredRent': str(savedData.offered_rent),
            'ownerEmail':User.objects.get(id=savedData.owner_id_id).email
        }

        rabbit_producer.send_message(json_data, routing_key='booking_alert_key', exchange='rabbitmq_exchange')
        rabbit_producer.close_connection()


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
                for each in data:
                    # location_with_room = Location.objects.filter(id=uuid_object).prefetch_related(
                    #     'room__room_images').first()
                    # serialized_data = {
                    #     'location': serialize('json', [location_with_room], use_natural_foreign_keys=True),
                    #     'room': serialize('json', [location_with_room.room], use_natural_foreign_keys=True),
                    #     'image': serialize('json', location_with_room.room.room_images.all())
                    # }
                    # return_data.append(serialized_data)

                    uuid_object = each['uuid']
                    # //Search for the locaiton
                    roomLocation = Location.objects.filter(id=uuid_object).get()
                    roomDetails = Room.objects.filter(id=roomLocation.room_id).get()
                    imageLink = RoomImage.objects.filter(room_id=roomDetails.id).get()
                    owner = User.objects.filter(id=roomDetails.user_id).get()

                    if roomDetails.available:
                        return_data.append({'roomId': roomDetails.id,
                                            'roomType': roomDetails.room_type,
                                            'roomOwner': roomDetails.user_id,
                                            'noOfRooms': roomDetails.no_of_room,
                                            'bathroomType': roomDetails.bathroom_type,
                                            'kitchenSlab': roomDetails.kitchen_slab,
                                            'wifi': roomDetails.wifi,
                                            'waterType': roomDetails.water_type,
                                            'description': roomDetails.description,
                                            'imageLink': str(imageLink.room_image),
                                            'latitude': roomLocation.latitude,
                                            'longitude': roomLocation.longitude,
                                            'locationName': roomLocation.name,
                                            'available': roomDetails.available,
                                            'rent': roomDetails.rent,
                                            'distance': each['distance'],
                                            'ownerName': owner.first_name + " " + owner.last_name
                                            })

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
        user_id = request.user.id

        all_rooms = Room.objects.filter(user_id=user_id).prefetch_related()
        rooms_list = []

        for room in all_rooms:
            image_link = RoomImage.objects.filter(room_id=room.id).first()
            room_location = Location.objects.filter(room_id=room.id).first()

            if image_link and room_location:
                image_url = str(image_link.room_image) if image_link.room_image else None

                rooms_list.append({
                    'id': room.id,
                    'roomType': room.room_type,
                    'noOfRooms': room.no_of_room,
                    'user_id': room.user_id,
                    'bathroomType': room.bathroom_type,
                    'kitchenSlab': room.kitchen_slab,
                    'wifi': room.wifi,
                    'waterType': room.water_type,
                    'description': room.description,
                    'imageLink': image_url,
                    'coordinates': f"{room_location.latitude}, {room_location.longitude}",
                    'locationName': room_location.name
                })

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
                 'remarks': room.remarks,
                 'expectedDate': room.rented_date,
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


# Accept the Booking Request
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
            "owner": {
                "name": request.user.username,
                "email": request.user.email,
                "phone": request.user.phone,
                "address": request.user.address
            },
            "room": {
                "location": locationDetails.name,
                "rent": str(roomDetails.rent),
                "bathroomType": roomDetails.bathroom_type,
                "kitchenSlab": "Yes" if roomDetails.kitchen_slab else "No"
            },
            "tenant": {
                "name": tenant_user.username,
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


class RoomDetailsAPIView(APIView):
    def get(self, request):
        try:
            roomId = request.query_params.get('roomId')
            roomDetails = Room.objects.get(id=roomId)
            location = Location.objects.get(room_id=roomId)
            images = RoomImage.objects.get(room_id=roomId)
            print("Location", location)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        except Location.DoesNotExist:
            return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)

        room_serializer = RoomSerializer(roomDetails)
        location_serializer = LocationSerializer(location)

        response_data = {
            'roomId': roomDetails.id,
            'roomType': roomDetails.room_type,
            'noOfRooms': roomDetails.no_of_room,
            'bathroomType': roomDetails.bathroom_type,
            'kitchenSlab': roomDetails.kitchen_slab,
            'wifi': roomDetails.wifi,
            'waterType': roomDetails.water_type,
            'imageLink': "http://localhost:8000/media/" + str(images.room_image),
            'latitude': location.latitude,
            'longitude': location.longitude,
            'locationName': location.name,
            'rent': roomDetails.rent,
            'description': roomDetails.description,
            'ownerId': roomDetails.user_id

        }

        return Response(response_data)


# ********************* USER PROFILE &************************
class GetUserdetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # userProfile = UserProfilePicture.objects.get(user=user)
        # userDocument = DocumentUpload.objects.get(user=user)

        returnData = {
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "verification":user.verification
            # "image": userProfile.profile_picture.url,
            # "documentType":userDocument.document_type,
            # "documentImage": userDocument.document_image.url
        }

        return JsonResponse(returnData, status=status.HTTP_200_OK, safe=False)


# Get users profile picture
class GetUserProfilePictureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            userProfile = UserProfilePicture.objects.get(user=user)

            returnData = {
                "image": userProfile.profile_picture.url,
            }
            return JsonResponse(returnData, status=status.HTTP_200_OK, safe=False)
        except:
            returnData = {
                "image": None,
            }
            return JsonResponse(None,  status=status.HTTP_200_OK, safe=False)


# Get Document picture
class GetDocumentPictureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            userDocument = DocumentUpload.objects.get(user=user)

            returnData = {
                "documentType": userDocument.document_type,
                "documentImage": userDocument.document_image.url,
                "verificationStatus":userDocument.verification_status
            }
            return JsonResponse(returnData, status=status.HTTP_200_OK, safe=False)
        except:
            # returnData = {
            #     "documentType": None,
            #     "documentImage": None
            # }
            return JsonResponse( None, status=status.HTTP_200_OK, safe=False)


class GetUserRequestedRoom(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        userRentedRoomRequest = RentedRoom.objects.filter(tenant_id_id=user.id)

        returnData = []

        for each in userRentedRoomRequest:
            roomDetails = Room.objects.get(id=each.room_id_id)
            locationDetails = Location.objects.get(room_id=each.room_id_id)

            returnData.append({
                'roomId': roomDetails.id,
                'bookingTableId': each.id,
                'locationName': locationDetails.name,
                'coordinate': str(locationDetails.latitude) + ", " + str(locationDetails.longitude),
                'roomType': roomDetails.room_type,
                'noOfRooms': roomDetails.no_of_room,
                'bathroomType': roomDetails.bathroom_type,
                'kitchenType': roomDetails.kitchen_slab,
                'wifi': roomDetails.wifi,
                'water': roomDetails.water_type,
                'rent': roomDetails.rent,
                'status': each.status,
                'offeredRent': each.offered_rent
            })

        return JsonResponse(returnData, status=status.HTTP_200_OK, safe=False)


class CancelBookingRequest(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookingTableId = request.query_params.get('id')
        bookingTable = RentedRoom.objects.get(id=bookingTableId)

        bookingTable.status = "CANCELLED"
        bookingTable.save(update_fields=['status'])

        return JsonResponse("Cancelled Booking Request", status=status.HTTP_200_OK, safe=False)


class GetAvailableRoomLocation(APIView):
    def get(self, request):
        available_rooms = Room.objects.filter(available=True)
        return_data = []

        for room in available_rooms:
            location = Location.objects.filter(room_id=room.id).first()
            if location:
                return_data.append({
                    "latitude": location.latitude,
                    "longitude": location.longitude
                })

        return JsonResponse(return_data, status=status.HTTP_200_OK, safe=False)



##################### ADMIN VIEW ##########################
#Get the users details with their documents to view in admin page
class GetDocumentWithUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        documentStatus = request.query_params.get('status')

        retrievedDocuments = DocumentUpload.objects.filter(verification_status=documentStatus)

        returnData = []

        for each in retrievedDocuments:
            userDetails = User.objects.get(id=each.user_id)

            returnData.append({
                "userId":userDetails.id,
                "documentId":each.id,
                "documentType":each.document_type,
                "documentImage":each.document_image.url,
                "userName":userDetails.first_name + " " + userDetails.last_name,
                "userEmail":userDetails.email,
                "userPhone":userDetails.phone,
                "userAddress":userDetails.address,
                "status":each.verification_status
            })
        return JsonResponse(returnData, status=status.HTTP_200_OK, safe=False)

#The admin can view and accept/reject the document.
class PerformActionOnDocument(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        documentId = request.query_params.get('id')
        newStatus = request.query_params.get('status')


        #Update the document status
        document = DocumentUpload.objects.get(id=documentId)
        document.verification_status = newStatus
        document.save(update_fields=['verification_status'])

        #update the user
        if(newStatus == "APPROVED"):
            user = User.objects.get(id=document.user_id)
            user.verification = True
            user.save(update_fields=['verification'])

        return JsonResponse("Document has been updated with status " + newStatus, status=status.HTTP_200_OK, safe=False)


#Get's All the user's details
class GetAllUserDetails(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type = request.query_params.get('type')

        #Get all users with role id 1 i.e. Tenant
        allUsers = None
        if type =='tenant':
            allUsers = User.objects.filter(role_id=3)
        elif type =='owner':
            allUsers = User.objects.filter(role_id=4)

        returnData = []

        for each in allUsers:
            print("Loop")
            returnData.append({
                "userId":each.id,
                "userName":each.first_name + " " + each.last_name,
                "userEmail":each.email,
                "userPhone":each.phone,
                "userAddress" : each.address
            })

        # for each in allOwner:
        #     print("Loop")
        #     owner.append({
        #         "userId": each.id,
        #         "userName": each.first_name + " " + each.last_name,
        #         "userEmail": each.email,
        #         "userPhone": each.phone,
        #         "userAddress": each.address,
        #         "userAddress": each.address,
        #         "verification" : each.verification
        #     })

        return JsonResponse(returnData, status=status.HTTP_200_OK, safe=False)


#Get the total, available, rented rooms count
class GetRoomCount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    #TODO: IMplement this
    def get(self, request):
        totalBookingRequest = len(RentedRoom.objects.all())
        acceptedRoomCount = len(RentedRoom.objects.filter(status="ACCEPTED"))
        rejectedRoomCount = len(RentedRoom.objects.filter(status="REJECTED"))
        cancelledRoomCount = len(RentedRoom.objects.filter(status="CANCELLED"))
        pendingRoomCount = len(RentedRoom.objects.filter(status="PENDING"))
        totalRoomCount = len(Room.objects.all())
        availableRoomCount = len(Room.objects.filter(available=True))
        rentedRoomCount = len(Room.objects.filter(available=False))


        return JsonResponse({
            "totalBookingRequest": totalBookingRequest,
            "acceptedBookingCount":acceptedRoomCount,
            "rejectedBookingCount":rejectedRoomCount,
            "cancelledBookingCount":cancelledRoomCount,
            "pendingBookingCount":pendingRoomCount,
            "totalRoomCount":totalRoomCount ,
            "availableRoomCount":availableRoomCount,
            "rentedRoomCount":rentedRoomCount
        }, status=status.HTTP_200_OK, safe=False)


class DeleteUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('userId')

        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response("User deleted", status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response("Failed deleting user: {}".format(str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

################## ADMIN VIEW END #########################

class GetUserVerification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        return JsonResponse({"userVerification":user.verification}, status=status.HTTP_200_OK, safe=False)



class UpdateRoomDetails(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        room_id = request.query_params.get('id')

        # Get the room object based on the provided ID
        room = get_object_or_404(Room, id=room_id)

        # Update the room details based on the form data
        room.room_type = request.data.get('room_type')
        room.no_of_room = request.data.get('no_of_room')
        room.bathroom_type = request.data.get('bathroom_type')
        room.kitchen_slab = request.data.get('kitchen_slab')
        room.rent = request.data.get('rent')
        room.available = True
        room.wifi = request.data.get('wifi')
        room.water_type = request.data.get('water_type')
        room.description = request.data.get('description')

        # Save the updated room details
        room.save()

        return Response(
            {
                "message": "Room details updated successfully."
            },
            status=status.HTTP_200_OK
        )
