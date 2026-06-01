from django.urls import path
from . import views

urlpatterns = [
    # Email/Password auth
    path('signup/',           views.signup,           name='signup'),
    path('verify/',           views.verify,           name='verify'),
    path('verify-account/',   views.verify_account,   name='verify-account'),
    path('login/',            views.login,            name='login'),
    path('resend-otp/',       views.resend_otp,       name='resend-otp'),

    # OAuth auth
    path('oauth/callback/',   views.oauth_callback,   name='oauth-callback'),
    path('verify-phone/',     views.verify_phone_only,name='verify-phone-only'),

    # Shared
    path('me/',               views.me,               name='me'),
    path('logout/',           views.logout,           name='logout'),

    # ── Profile self-service (new) ──
    path('profile/',          views.profile,          name='profile'),
    path('change-password/',  views.change_password,  name='change-password'),
]