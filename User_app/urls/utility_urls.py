# app/urls/utility_urls.py
from django.urls import path

from User_app.views.utility_views import (
    get_dashboard_data, APICallCountView
)

app_name = 'utility'

urlpatterns = [
    path('dashboard/', get_dashboard_data, name='dashboard'),
    path('api-call-count/', APICallCountView.as_view(), name='api_call_count'),
]
