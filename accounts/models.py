from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class Role(models.Model):
    OWNER = 'Owner'
    TENANT = 'Tenant'
    ADMIN = 'Admin'
    name = models.CharField(max_length=100)
    
    def is_owner(self, user):
        return user.role == self.OWNER
    
    def is_tenant(self, user):
        return user.role == self.TENANT

    def is_admin(self, user):
        return user.role == self.ADMIN
    
    
class User(AbstractUser):
    id = models.UUIDField(default= uuid.uuid4, editable = False, primary_key = True)
    address = models.CharField(max_length = 200)
    phone = models.CharField(max_length=15 , null = False)
    verification = models.BooleanField(default =False)
    email = models.EmailField(unique = True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)