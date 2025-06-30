from django.urls import path
from User_app.views.garnishment_creditor_views import (
    CreditorDebtEditPermissionAPIView, CreditorDebtRuleAPIView,  CreditorDebtAppliedRuleAPIView, CreditorDebtExemptAmtConfigAPIView
)

app_name = 'garnishment_creditor'

urlpatterns = [

    # API for returning the rule of creditor debt based on case id
    path('creditor-debt-applied-rule/<str:case_id>/',
         CreditorDebtAppliedRuleAPIView.as_view(), name='creditor-debt-rule'),

    # CRUD for the Creditor debt exempt amt config
    path('creditor-debt-exempt-amt-config/', CreditorDebtExemptAmtConfigAPIView.as_view(),
         name='creditor-debt-exempt-amt-config'),
    path('creditor-debt-exempt-amt-config/<str:state>/<str:pay_period>/',
         CreditorDebtExemptAmtConfigAPIView.as_view(), name='creditor-debt-exempt-amt-config'),
    path('creditor-debt-exempt-amt-config/<str:state>/',
         CreditorDebtExemptAmtConfigAPIView.as_view(), name='creditor-debt-exempt-amt-config'),

    # CRUD for the creditor debt rule
    path('creditor-debt-rule/', CreditorDebtRuleAPIView.as_view(),
         name='creditor-debt-exempt-amt-config'),
    path('creditor-debt-rule/<str:state>/', CreditorDebtRuleAPIView.as_view(),
         name='creditor-debt-exempt-amt-config'),

    # This is for the state tax levy rule edit request
    path('creditor-debt-rule-edit-request/', CreditorDebtEditPermissionAPIView.as_view(),
         name='StateTaxLevyRuleEditPermissionAPIView'),
    path('creditor-debt-rule-edit-request/<str:state>/',
         CreditorDebtEditPermissionAPIView.as_view(), name='StateTaxLevyRuleEditPermissionAPIView'),


]
