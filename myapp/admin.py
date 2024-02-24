from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(UserProfilePicture)
class AdminUserProfilePicture(admin.ModelAdmin):
    list_display = ['id', 'user', 'profile_picture']


@admin.register(DocumentUpload)
class AdminDocumentUplaod(admin.ModelAdmin):
    list_display = ['id', 'user', 'document_type', 'document_image']


@admin.register(Room)
class AdminRoom(admin.ModelAdmin):
    list_display = ['id', 'user', 'room_type', 'no_of_room', 'bathroom_type', 'kitchen_slab', 'created_date', 'rent',
                    'available', 'wifi', 'water_type']


@admin.register(RoomImage)
class AdminRoomImage(admin.ModelAdmin):
    list_display = ['id', 'user', 'room', 'room_image']


@admin.register(Location)
class AdminLocation(admin.ModelAdmin):
    list_display = ['id', 'name', 'longitude', 'latitude']


