from django.urls import path
from . import views

urlpatterns = [
    # Email/Password auth
    path('signup/',         views.signup,            name='signup'),
    path('verify/',         views.verify,            name='verify'),
    path('login/',          views.login,             name='login'),
    path('resend-otp/',     views.resend_otp,        name='resend-otp'),


    # OAuth auth
    path('oauth/callback/', views.oauth_callback,    name='oauth-callback'),
    path('verify-phone/',   views.verify_phone_only, name='verify-phone-only'),

    # Shared
    path('me/',             views.me,                name='me'),

    #logout
    path('logout/', views.logout, name='logout'),
]