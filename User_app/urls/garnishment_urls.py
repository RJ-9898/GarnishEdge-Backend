# app/urls/garnishment_urls.py
from django.urls import path
from User_app.views.garnishment_views import (
    InsertIWODetailView, ConvertExcelToJsonView,
    GarnishmentOrderImportView, LastFiveLogsView,
    UpsertGarnishmentOrderView, ExportGarnishmentOrderDataView, GarnishmentFeesRules,
    ChildSupportCalculationRules, PDFUploadView, GETIWOPDFData,
    GarnishmentOrderDetails
)
from User_app.views.garnishment_calculation_views import PostCalculationView

app_name = 'garnishment'

urlpatterns = [
    path('iwo-data/', InsertIWODetailView.as_view(), name='iwo_data'),

    # Excel to JSON convert API
    path('convert-excel/', ConvertExcelToJsonView.as_view(), name='convert_excel'),

    # Import Order using excel
    path('import-orders/', GarnishmentOrderImportView.as_view(), name='import_orders'),

    # Showing the last five application activities
    path('logs/', LastFiveLogsView.as_view(), name='logs'),

    # Insert+Update order details using excel
    path('upsert-orders/', UpsertGarnishmentOrderView.as_view(), name='upsert_orders'),

    # Export garnishment order data in excel
    path('export-orders/', ExportGarnishmentOrderDataView.as_view(),
         name='export_orders'),

    # Garnishment calculation for api all types
    path('calculate/', PostCalculationView.as_view(), name='calculate'),

    # Child support calculation rule
    path('calculation-rules/<str:state>/<str:employee_id>/<str:supports_2nd_family>/<str:arrears_of_more_than_12_weeks>/<str:de>/<int:no_of_order>/',
         ChildSupportCalculationRules.as_view(), name='calculation_rules'),

    # PDF Data
    path('upload-pdf/', PDFUploadView.as_view(), name='upload_pdf'),
    path('get-pdf-data/', GETIWOPDFData.as_view(), name='get_pdf_data'),

    # CRUD for the garnishment order
    path('order-details/', GarnishmentOrderDetails.as_view(), name='order_details'),
    path('order-details/<str:case_id>/',
         GarnishmentOrderDetails.as_view(), name='delete_order'),

    # CRUD for the Garnishment fees rules
    path('fees-rules/<str:rule>/',
         GarnishmentFeesRules.as_view(), name='fees_rules'),
    path('fees-rules/', GarnishmentFeesRules.as_view(), name='fees_rules'),


]
