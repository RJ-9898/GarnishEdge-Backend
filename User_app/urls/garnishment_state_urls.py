# app/urls/garnishment_urls.py
from django.urls import path

from User_app.views.garnishment_state_views import (
    GarnishmentFeesRulesByState, StateTaxLevyConfigAPIView, StateTaxLevyExemptAmtConfigAPIView,
    StateTaxLevyAppliedRuleAPIView, StateTaxLevyRuleEditPermissionAPIView,
)
from User_app.views.garnishment_calculation_views import PostCalculationView

app_name = 'garnishment_state'

urlpatterns = [

    # CRUD for the state tax levy config
    path('state-tax-levy-config-data/',
         StateTaxLevyConfigAPIView.as_view(), name='StateTaxLevyRule'),
    path('state-tax-levy-config-data/<str:state>/',
         StateTaxLevyConfigAPIView.as_view(), name='StateTaxLevyRule'),

    # CRUD for the state tax levy rule edit request
    path('state-tax-levy-rule-edit-request/', StateTaxLevyRuleEditPermissionAPIView.as_view(),
         name='StateTaxLevyRuleEditPermissionAPIView'),
    path('state-tax-levy-rule-edit-request/<str:state>/',
         StateTaxLevyRuleEditPermissionAPIView.as_view(), name='StateTaxLevyRuleEditPermissionAPIView'),

    # CRUD for the Garnishment fees rules by state
    path('fees-rules-state/<str:state>/',
         GarnishmentFeesRulesByState.as_view(), name='fees_rules_state'),
    path('fees-rules-state/', GarnishmentFeesRulesByState.as_view(),
         name='fees_rules_state'),

    # CRUD for the state tax levy rule
    path('state-tax-levy-applied-rule/<str:case_id>/',
         StateTaxLevyAppliedRuleAPIView.as_view(), name='StateTaxLevyRuleAPIView'),

    # CRUD for the state tax levy exempt amt config
    path('state-tax-levy-exempt-amt-config/', StateTaxLevyExemptAmtConfigAPIView.as_view(),
         name='StateTaxLevyRuleEditPermissionAPIView'),
    path('state-tax-levy-exempt-amt-config/<str:state>/',
         StateTaxLevyExemptAmtConfigAPIView.as_view(), name='StateTaxLevyRuleEditPermissionAPIView'),
    path('state-tax-levy-exempt-amt-config/<str:state>/<str:pay_period>/',
         StateTaxLevyExemptAmtConfigAPIView.as_view(), name='StateTaxLevyRuleEditPermissionAPIView'),


]
