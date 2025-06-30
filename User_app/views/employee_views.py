from User_app.exception_handler import log_and_handle_exceptions
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from openpyxl import Workbook
from GarnishEdge_Project.garnishment_library.utility_class import ResponseHelper
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from io import BytesIO
import pandas as pd
import math
import csv
from rest_framework.response import Response
from rest_framework.views import APIView
from User_app.models import employee_detail, garnishment_order, garnishment_fees
from ..serializers import EmployeeDetailsSerializer
from datetime import datetime
from User_app.constants import (
    EmployeeFields as EE,
    GarnishmentTypeFields as GT,
    CalculationFields as CA,
    PayrollTaxesFields as PT,
    CalculationResponseFields as CR,
    CommonConstants,
    ResponseMessages,
    BatchDetail
)


class EmployeeImportView(APIView):
    """
    Handles the import of employee details from an Excel or CSV file.
    """
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Excel or CSV file to upload"
            ),
            openapi.Parameter(
                name='title',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="Optional title"
            )
        ],
        responses={200: "File uploaded successfully",
                   400: "Row import error",
                   500: "Internal server error"},
    )
    def post(self, request):
        try:
            if 'file' not in request.FILES:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
            file = request.FILES['file']
            file_name = file.name

            # Read file based on extension
            if file_name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt')):
                df = pd.read_excel(file)
            else:
                return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)

            employees = []
            for _, row in df.iterrows():
                try:
                    employee_data = {
                        EE.EMPLOYEE_ID: row.get(EE.EMPLOYEE_ID),
                        EE.CASE_ID: row.get(EE.CASE_ID),
                        EE.AGE: row.get(EE.AGE),
                        EE.SSN: row.get(EE.SSN),
                        EE.IS_BLIND: row.get(EE.IS_BLIND),
                        EE.HOME_STATE: row.get(EE.HOME_STATE),
                        EE.WORK_STATE: row.get(EE.WORK_STATE),
                        EE.GENDER: row.get(EE.GENDER),
                        EE.PAY_PERIOD: row.get(EE.PAY_PERIOD),
                        EE.NO_OF_EXEMPTION_INCLUDING_SELF: row.get(EE.NO_OF_EXEMPTION_INCLUDING_SELF),
                        EE.FILING_STATUS: row.get(EE.FILING_STATUS),
                        EE.MARITAL_STATUS: row.get(EE.MARITAL_STATUS),
                        EE.NO_OF_STUDENT_DEFAULT_LOAN: row.get(EE.NO_OF_STUDENT_DEFAULT_LOAN),
                        EE.SUPPORT_SECOND_FAMILY: row.get(EE.SUPPORT_SECOND_FAMILY),
                        EE.SPOUSE_AGE: row.get(EE.SPOUSE_AGE),
                        EE.IS_SPOUSE_BLIND: row.get(EE.IS_SPOUSE_BLIND),
                        EE.GARNISHMENT_FEES_STATUS: row.get(EE.GARNISHMENT_FEES_STATUS),
                        EE.GARNISHMENT_FEES_SUSPENDED_TILL: row.get(EE.GARNISHMENT_FEES_SUSPENDED_TILL),
                    }
                    serializer = EmployeeDetailsSerializer(data=employee_data)
                    if serializer.is_valid():
                        employees.append(serializer.save())
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                except Exception as row_exc:
                    return Response({"error": f"Row import error: {row_exc}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "File processed Successfully", "status code": status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})


class EmployeeDetailsAPIViews(APIView):
    """
    API view for CRUD operations on employee details.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Success', EmployeeDetailsSerializer(many=True)),
            404: 'Employee not found',
            500: 'Internal server error'
        }
    )

    def get(self, request, case_id=None, ee_id=None):
        """
        Retrieve employee details by case_id and ee_id, or all employees if not provided.
        """
        try:
            if case_id and ee_id:
                try:
                    employee = employee_detail.objects.get(
                        case_id=case_id, ee_id=ee_id)
                    serializer = EmployeeDetailsSerializer(employee)
                    return ResponseHelper.success_response('Employee data fetched successfully', serializer.data)
                except employee_detail.DoesNotExist:
                    return ResponseHelper.error_response(
                        f'Employee with case_id "{case_id}" and ee_id "{ee_id}" not found',
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            else:
                employees = employee_detail.objects.all()
                serializer = EmployeeDetailsSerializer(employees, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)
        except Exception as e:
            return ResponseHelper.error_response(
                'Failed to fetch data',
                str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=EmployeeDetailsSerializer,
        responses={
            201: openapi.Response('Created', EmployeeDetailsSerializer),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new employee detail record.
        """
        try:
            serializer = EmployeeDetailsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response(
                    'Data created successfully',
                    serializer.data,
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return ResponseHelper.error_response(
                    'Invalid data',
                    serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return ResponseHelper.error_response(
                'Internal server error while creating data',
                str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=EmployeeDetailsSerializer,
        responses={
            200: openapi.Response('Updated', EmployeeDetailsSerializer),
            400: 'Invalid data or missing identifiers',
            404: 'Employee not found',
            500: 'Internal server error'
        }
    )
    def put(self, request, case_id=None, ee_id=None):
        """
        Update an existing employee detail record by case_id and ee_id.
        """
        if not case_id or not ee_id:
            return ResponseHelper.error_response(
                'Case ID and Employee ID are required in URL to update data',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            employee = employee_detail.objects.get(
                case_id=case_id, ee_id=ee_id)
        except employee_detail.DoesNotExist:
            return ResponseHelper.error_response(
                f'Employee with case_id "{case_id}" and ee_id "{ee_id}" not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        try:
            serializer = EmployeeDetailsSerializer(employee, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response(
                    'Data updated successfully',
                    serializer.data
                )
            else:
                return ResponseHelper.error_response(
                    'Invalid data',
                    serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return ResponseHelper.error_response(
                'Internal server error while updating data',
                str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={
            200: 'Employee deleted successfully',
            400: 'Case ID and Employee ID are required in URL to delete data',
            404: 'Employee not found',
            500: 'Internal server error'
        }
    )
    def delete(self, request, case_id=None, ee_id=None):
        """
        Delete an employee detail record by case_id and ee_id.
        """
        if not case_id or not ee_id:
            return ResponseHelper.error_response(
                'Case ID and Employee ID are required in URL to delete data',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            employee = employee_detail.objects.get(
                case_id=case_id, ee_id=ee_id)
            employee.delete()
            return ResponseHelper.success_response(
                f'Employee with case_id "{case_id}" and ee_id "{ee_id}" deleted successfully'
            )
        except employee_detail.DoesNotExist:
            return ResponseHelper.error_response(
                f'Employee with case_id "{case_id}" and ee_id "{ee_id}" not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return ResponseHelper.error_response(
                'Internal server error while deleting data',
                str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpsertEmployeeDataView(APIView):
    """
    API endpoint to upsert (insert or update) employee details from an uploaded Excel or CSV file.
    Provides robust exception handling and clear response messages.
    """
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Excel or CSV file to upload"
            ),
            openapi.Parameter(
                name='title',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="Optional title"
            )
        ],
        responses={
            200: 'File uploaded and processed successfully',
            400: 'No file uploaded or unsupported file format',
            500: 'Internal server error'
        },
    )
    def post(self, request):
        """
        Upsert employee details from uploaded file.
        """
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read file data based on extension
            if file.name.endswith('.csv'):
                data = list(csv.DictReader(
                    file.read().decode('utf-8').splitlines()))
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
                data = df.to_dict(orient='records')
            else:
                return Response({'error': 'Unsupported file format. Use CSV or Excel.'}, status=status.HTTP_400_BAD_REQUEST)

            added_employees, updated_employees = [], []

            for row in data:
                # Remove unnamed columns and handle NaN social security numbers
                row = {k: v for k, v in row.items() if k and not str(
                    k).startswith('Unnamed')}
                row = {
                    k: ("" if (k == "social_security_number" and isinstance(
                        v, float) and math.isnan(v)) else v)
                    for k, v in row.items()
                }

                # Parse and format date fields
                date_field = row.get("garnishment_fees_suspended_till")
                if date_field:
                    try:
                        if isinstance(date_field, datetime):
                            row["garnishment_fees_suspended_till"] = date_field.strftime(
                                "%Y-%m-%d")
                        else:
                            parsed_date = pd.to_datetime(
                                date_field, errors='coerce')
                            row["garnishment_fees_suspended_till"] = parsed_date.strftime(
                                "%Y-%m-%d") if not pd.isnull(parsed_date) else None
                    except Exception:
                        row["garnishment_fees_suspended_till"] = None

                case_id = row.get("case_id")
                ee_id = row.get("ee_id")
                if not ee_id or not case_id:
                    continue  # Skip if identifiers are missing

                # Normalize boolean fields
                boolean_fields = ['is_blind',
                                  'is_spouse_blind', 'support_second_family']
                for bfield in boolean_fields:
                    val = row.get(bfield)
                    if isinstance(val, str):
                        row[bfield] = val.strip().lower() in [
                            'true', '1', 'yes']

                # Check if employee exists
                obj_qs = employee_detail.objects.filter(
                    case_id=case_id, ee_id=ee_id)
                obj = obj_qs.first() if obj_qs.exists() else None

                if obj:
                    # Update only if there are changes
                    has_changes = any(
                        str(getattr(obj, field, '')).strip() != str(
                            row.get(field, '')).strip()
                        for field in row.keys()
                        if hasattr(obj, field)
                    )
                    if has_changes:
                        serializer = EmployeeDetailsSerializer(
                            obj, data=row, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            updated_employees.append(ee_id)
                else:
                    serializer = EmployeeDetailsSerializer(data=row)
                    if serializer.is_valid():
                        serializer.save()
                        added_employees.append(ee_id)

            response_data = []
            if added_employees:
                response_data.append({
                    'message': 'Employee(s) imported successfully',
                    'added_employees': added_employees
                })
            if updated_employees:
                response_data.append({
                    'message': 'Employee details updated successfully',
                    'updated_employees': updated_employees
                })

            if not response_data:
                return Response({
                    'success': True,
                    'status_code': status.HTTP_200_OK,
                    'message': 'No data was updated or inserted.'
                }, status=status.HTTP_200_OK)

            return Response({
                'success': True,
                'status_code': status.HTTP_200_OK,
                'response_data': response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # logger.error(f"Error upserting employee data: {e}")
            return Response({
                'success': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Export employee details using the Excel file
class ExportEmployeeDataView(APIView):
    """
    Exports employee details as an Excel file.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: 'Employee data exported successfully as Excel file',
            404: 'No employees found',
            500: 'Internal server error'
        }
    )
    def get(self, request):
        try:
            employees = employee_detail.objects.all()
            if not employees.exists():
                return JsonResponse(
                    {'detail': 'No employees found',
                        'status': status.HTTP_404_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = EmployeeDetailsSerializer(employees, many=True)

            # Define Excel workbook and worksheet
            wb = Workbook()
            ws = wb.active
            ws.title = "Employee Data"

            # Define headers using constants where available
            header_fields = [
                EE.EMPLOYEE_ID, EE.SSN, EE.AGE, EE.GENDER, EE.HOME_STATE, EE.WORK_STATE,
                EE.CASE_ID, EE.PAY_PERIOD, EE.IS_BLIND, EE.MARITAL_STATUS, EE.FILING_STATUS, EE.SPOUSE_AGE,
                EE.IS_SPOUSE_BLIND, EE.NO_OF_EXEMPTION_INCLUDING_SELF, EE.SUPPORT_SECOND_FAMILY,
                EE.NO_OF_STUDENT_DEFAULT_LOAN, EE.GARNISHMENT_FEES_STATUS, EE.GARNISHMENT_FEES_SUSPENDED_TILL
            ]
            ws.append(header_fields)

            # Append employee data
            for employee in serializer.data:
                row = [employee.get(field, '') for field in header_fields]
                ws.append(row)

            # Save workbook to in-memory buffer
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            # Prepare HTTP response with Excel content
            filename = f'employee_details_{datetime.today().strftime("%m-%d-%y")}.xlsx'
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            return JsonResponse(
                {'detail': f'Error exporting employee data: {str(e)}',
                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeGarnishmentOrderCombineData(APIView):
    """
    API endpoint to combine employee, garnishment order, and garnishment fee data.
    Returns merged data or appropriate error messages.
    """

    @swagger_auto_schema(
        responses={
            200: 'Combined data fetched successfully',
            204: 'No matching data found',
            400: 'Missing required columns',
            500: 'Internal server error'
        }
    )
    def get(self, request):
        try:
            # Fetch all records from the database
            employees = employee_detail.objects.all()
            garnishments = garnishment_order.objects.all()
            fees = garnishment_fees.objects.all()

            # Convert queryset to DataFrame for processing
            df_employees = pd.DataFrame(list(employees.values()))
            df_garnishments = pd.DataFrame(list(garnishments.values()))
            df_fees = pd.DataFrame(list(fees.values()))

            # Check for empty dataframes
            if df_employees.empty or df_garnishments.empty or df_fees.empty:
                return Response(
                    {"message": "No matching data found"},
                    status=status.HTTP_204_NO_CONTENT
                )

            # Define required columns for each DataFrame using constants where available
            required_columns_employees = {
                EE.EMPLOYEE_ID, EE.WORK_STATE, EE.PAY_PERIOD, EE.CASE_ID
            }
            required_columns_garnishments = {
                'eeid', EE.GARNISHMENT_TYPE, EE.CASE_ID}
            required_columns_fees = {
                'state', EE.GARNISHMENT_TYPE, EE.PAY_PERIOD, 'rules'}

            # Validate required columns
            if not required_columns_employees.issubset(df_employees.columns) or \
               not required_columns_garnishments.issubset(df_garnishments.columns) or \
               not required_columns_fees.issubset(df_fees.columns):
                return Response(
                    {"message": "Missing required columns"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Normalize string columns for consistent merging
            df_employees[EE.WORK_STATE] = df_employees[EE.WORK_STATE].astype(
                str).str.strip().str.lower()
            df_employees[EE.PAY_PERIOD] = df_employees[EE.PAY_PERIOD].astype(
                str).str.strip().str.lower()
            df_employees[EE.EMPLOYEE_ID] = df_employees[EE.EMPLOYEE_ID].astype(
                str).str.strip()
            df_employees[EE.CASE_ID] = df_employees[EE.CASE_ID].astype(
                str).str.strip()

            df_garnishments[EE.GARNISHMENT_TYPE] = df_garnishments[EE.GARNISHMENT_TYPE].astype(
                str).str.strip().str.lower()
            df_garnishments['eeid'] = df_garnishments['eeid'].astype(
                str).str.strip()
            df_garnishments[EE.CASE_ID] = df_garnishments[EE.CASE_ID].astype(
                str).str.strip()

            df_fees['state'] = df_fees['state'].astype(
                str).str.strip().str.lower()
            df_fees[EE.GARNISHMENT_TYPE] = df_fees[EE.GARNISHMENT_TYPE].astype(
                str).str.strip().str.lower()
            df_fees[EE.PAY_PERIOD] = df_fees[EE.PAY_PERIOD].astype(
                str).str.strip().str.lower()

            # Merge employee and garnishment order data on ee_id/case_id
            merged_df = df_employees.merge(
                df_garnishments[['eeid', EE.CASE_ID, EE.GARNISHMENT_TYPE]],
                left_on=[EE.EMPLOYEE_ID, EE.CASE_ID],
                right_on=['eeid', EE.CASE_ID],
                how='left'
            ).drop(columns=['eeid'])

            # Merge with fees data on work_state/type/pay_period
            final_df = merged_df.merge(
                df_fees[['state', EE.GARNISHMENT_TYPE, EE.PAY_PERIOD, 'rules']],
                left_on=[EE.WORK_STATE, EE.GARNISHMENT_TYPE, EE.PAY_PERIOD],
                right_on=['state', EE.GARNISHMENT_TYPE, EE.PAY_PERIOD],
                how='left'
            ).drop(columns=['state'])

            # Replace NaN with None for JSON serialization
            data = final_df.where(pd.notna(final_df),
                                  None).to_dict(orient='records')

            response_data = {
                'success': True,
                'message': 'Data fetched successfully',
                'status_code': status.HTTP_200_OK,
                "data": data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred while processing the data: {str(e)}",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
