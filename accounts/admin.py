from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'address', 'phone', 'verification', 'role_id']
