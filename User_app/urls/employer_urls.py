# app/urls/employer_urls.py
from django.urls import path
from User_app.views.employer_views import (
    EmployerDetails, GETSettingDetails, SettingPostAPI
)

app_name = 'employer'

urlpatterns = [

    # CRUD
    path('details/', EmployerDetails.as_view(), name='details'),
    path('details/<int:id>/', EmployerDetails.as_view(), name='details'),

    # setting URL's
    path('settings/<int:id>/', GETSettingDetails.as_view(), name='settings_get'),
    path('settings/', SettingPostAPI, name='settings_post'),
]
