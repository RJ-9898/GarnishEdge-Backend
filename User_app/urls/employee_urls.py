# app/urls/employee_urls.py
from django.urls import path
from User_app.views.employee_views import (
 EmployeeDetailsAPIViews
    , EmployeeImportView,
     UpsertEmployeeDataView, ExportEmployeeDataView,EmployeeGarnishmentOrderCombineData)

app_name = 'employee'

urlpatterns = [

    #CRUD for the employee data
    path('details/', EmployeeDetailsAPIViews.as_view(), name='details'),
    path('details/<str:case_id>/<str:ee_id>/', EmployeeDetailsAPIViews.as_view(), name='details'),

    #Import employee using excel
    path('import/', EmployeeImportView.as_view(), name='import'),

    #Insert+Update Employee details using excel
    path('upsert/', UpsertEmployeeDataView.as_view(), name='upsert'),

    #Export employee data in excel
    path('export/', ExportEmployeeDataView.as_view(), name='export_employees'),

    #Get employee data 
    path('rules/', EmployeeGarnishmentOrderCombineData.as_view(), name='employee_rules'),
]
