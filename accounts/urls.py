from django.urls import path, include
from .views import *
urlpatterns = [
    path('register-owner/', OwnerSignUpView.as_view(), name='owner-signup'),
    path('register-tenant/', TenantSignUpView.as_view(), name='tenant-signup'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('get-user-role/', Getuserroleview.as_view(), name='user-role'),
    path('get-user-details/',GetUserdetailsView.as_view(), name='user-details'),
    path('logout/', LogOutView.as_view(), name='logout')
]
