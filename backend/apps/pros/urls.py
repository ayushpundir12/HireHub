from django.urls import path
from . import views

urlpatterns = [
    path('api/become-pro/', include('apps.become_pro.urls')),
]