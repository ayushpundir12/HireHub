from django.urls import path
from . import views

urlpatterns = [
    # Start & status
    path('apply/',   views.become_pro,          name='become-pro'),
    path('status/',  views.application_status,  name='application-status'),

    # Multi-step form
    path('step/personal/',      views.PersonalInfoView.as_view(),      name='step-personal'),
    path('step/service/',       views.ServiceInfoView.as_view(),       name='step-service'),
    path('step/kyc/',           views.KYCView.as_view(),               name='step-kyc'),
    path('step/pcc/',           views.PCCView.as_view(),               name='step-pcc'),
    path('step/skills/',        views.SkillCertificatesView.as_view(), name='step-skills'),
    path('step/location/',      views.LocationView.as_view(),          name='step-location'),

    # Submit
    path('submit/', views.submit_pro_application, name='submit-pro-application'),
]