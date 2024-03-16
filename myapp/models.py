import uuid

from django.contrib.auth import get_user_model
from django.db import models

from accounts.models import Role

User = get_user_model()


class UserProfilePicture(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, default='')
    profile_picture = models.ImageField(upload_to='profile_pic', blank=True, null=True)


class DocumentUpload(models.Model):
    class DocumentType(models.TextChoices):
        CITIZENSHIP = "CITIZENSHIP", "Citizenship"
        LISCENCE = "LICENCE", "Licence"

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default='', related_name='documents')
    document_type = models.CharField(max_length=200, choices=DocumentType.choices)
    document_image = models.ImageField(upload_to='document_pics')


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        FLAT = "FLAT", "Flat"
        MULTIPLE = "MULTIPLE", "Multiple"

    class BathroomType(models.TextChoices):
        ATTACHED = "ATTACHED", "Attached"
        SHARING = "SHARING", "Sharing"

    class WaterType(models.TextChoices):
        TANKER = "TANKER", "Tanker"
        BORING = "BORING", "Boring"
        MELAMCHI = "MELAMCHI", "Melamchi"

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, default='', on_delete=models.CASCADE)
    room_type = models.CharField(max_length=100, choices=RoomType.choices)
    no_of_room = models.IntegerField()
    bathroom_type = models.CharField(max_length=100, choices=BathroomType.choices)
    kitchen_slab = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    rent = models.DecimalField(max_digits=15, decimal_places=2)
    available = models.BooleanField(default=True)
    wifi = models.BooleanField(default=False)
    water_type = models.CharField(max_length=100, choices=WaterType.choices)
    description = models.TextField()



class RoomImage(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, default='', on_delete=models.CASCADE, null=True)
    room = models.ForeignKey(Room, default='', related_name='room_images', on_delete=models.CASCADE, null=True)
    room_image = models.ImageField(upload_to='room_images/')

    def __str__(self):
        return f"Image for Room {self.room} by {self.user.username}"


class Location(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=40, decimal_places=30)
    longitude = models.DecimalField(max_digits=40, decimal_places=30)
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='room')

    def __str__(self):
        return f"Location {self.id}"


class RentedRoom(models.Model):
    class StatusType(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        PENDING = "PENDING", "Pending"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    room_id = models.ForeignKey(Room, on_delete=models.CASCADE)
    owner_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    tenant_id = models.ForeignKey(User, default='', on_delete=models.CASCADE, related_name='tenant')
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=StatusType.choices, default="PENDING")
    rented_date = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    released_date = models.DateField(null=True)
    remarks = models.TextField(null=True)
    offered_rent = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Status for room {self.room_id} is {self.status}"


