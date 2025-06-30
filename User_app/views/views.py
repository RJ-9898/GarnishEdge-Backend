from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import *
from vercel_blob import put
from django.conf import settings
from openpyxl import Workbook
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from GarnishEdge_Project.garnishment_library.utility_class import *
from django.http import HttpResponse
import os
from io import BytesIO
import time
import random
import string
import pandas
import math
from User_app.models import *
from django.contrib.auth import login as auth_login, get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from django.shortcuts import get_object_or_404
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework.generics import DestroyAPIView, RetrieveUpdateAPIView
from ..serializers import *
from django.http import HttpResponse
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError
from rest_framework import status, permissions
import csv
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from User_app.models import employee_detail
import pandas as pd
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from User_app.models import garnishment_order, employee_detail
from GarnishEdge_Project.garnishment_library.child_support import *
from rest_framework_simplejwt.views import TokenRefreshView
from ..serializers import CustomTokenRefreshSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


@swagger_auto_schema(
    operation_description="Register a new user",
    request_body=EmployerProfileSerializer,
    responses={201: "User Created"}
)
class LoginAPIView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request):
        data = request.data

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response({'success': False, 'message': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Employer_Profile.objects.get(email=email)
        except Employer_Profile.DoesNotExist:
            return Response({'success': False, 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({'success': False, 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        # Auth login to register session (optional for non-session apps)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth_login(request, user)

        # Create tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({
            'success': True,
            'message': 'Login successful',
            'user_data': {
                "id": user.id,
                'username': user.username,
                'name': user.employer_name,
                'email': user.email,
            }
        }, status=status.HTTP_200_OK)

        # Set token cookies
        access_expire = datetime.utcnow() + timedelta(minutes=5)
        refresh_expire = datetime.utcnow() + timedelta(days=1)

        response.set_cookie(
            key='access',
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=False,
            expires=access_expire,
        )
        response.set_cookie(
            key='refresh',
            value=str(refresh),
            httponly=True,
            samesite='Lax',
            secure=False,
            expires=refresh_expire,
        )

        return response


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = EmployerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseHelper.success_response("Successfully registered", status_code=status.HTTP_201_CREATED)
        return ResponseHelper.error_response("Validation Failed", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh')

        if not refresh_token:
            return Response({"message": "No refresh token found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # Only works if blacklist app is enabled
        except TokenError:
            return ResponseHelper.error_response("Invalid or expired token", status_code=status.HTTP_400_BAD_REQUEST)

        # Clear the cookies
        response = ResponseHelper.success_response(
            "Logout successful", status_code=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response

# @csrf_exempt
# def EmployerProfile(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             if len(str(data['federal_employer_identification_number'])) != 9:
#                 return JsonResponse({'error': 'Federal Employer Identification Number must be exactly 9 characters long', 'status_code':status.HTTP_400_BAD_REQUEST})

#             if Employer_Profile.objects.filter(email=data['email']).exists():
#                 return JsonResponse({'error': 'Email already registered', 'status_code':status.HTTP_400_BAD_REQUEST})

#             user = Employer_Profile.objects.create(**data)

#             employee = get_object_or_404(Employer_Profile, cid=user.id)
#             LogEntry.objects.create(
#                 action='Employer details added',
#                 details=f'Employer details with ID {employee.employer_id}'
#             )
#             return JsonResponse({'message': 'Employer Detail Successfully Registered', "status code" :status.HTTP_201_CREATED})
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     else:
#         return JsonResponse({'message': 'Please use POST method','status code':status.HTTP_400_BAD_REQUEST})


class EmployeeDetailsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Deserialize and validate data using the serializer
            serializer = EmployeeDetailsSerializer(data=request.data)
            if not serializer.is_valid():

                return ResponseHelper.error_response("Validation Failed", serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

            # Save validated data to the database
            employee = serializer.save()

            # Log the action
            LogEntry.objects.create(
                action='Employee details added',
                details=f'Employee details added Successfully with employee ID {employee.ee_id}'
            )
            return ResponseHelper.success_response("Employee Details Successfully Registered", status_code=status.HTTP_201_CREATED)

        except Exception as e:  # Handle general errors
            return Response(
                {'error': str(e),
                 "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )

# update employee Details


@method_decorator(csrf_exempt, name='dispatch')
class EmployerProfileEditView(RetrieveUpdateAPIView):
    queryset = Employer_Profile.objects.all()
    serializer_class = EmployerProfileSerializer
    lookup_fields = ['id']

    def get_object(self):
        """
        Overriding `get_object` to fetch the instance based on multiple fields.
        """
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {field: self.kwargs[field]
                         for field in self.lookup_fields}

        obj = queryset.filter(**filter_kwargs).first()
        if not obj:
            raise Exception(f"Object not found with {filter_kwargs}")
        return obj

    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # Logging the update action
            LogEntry.objects.create(
                action='Details updated',
                details=f'Details updated Successfully for ID {instance.id}'
            )
            # Preparing the response data
            ResponseHelper.success_response(
                "Data updated Successfully", status_code=status.HTTP_200_OK)
            response_data = {
                'success;': True,
                'message': 'Data updated Successfully',
                'status_code': status.HTTP_200_OK
            }
            return JsonResponse(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse(
                {'error': str(
                    e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# update employee Details
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDetailsUpdateAPIView(RetrieveUpdateAPIView):
    queryset = employee_detail.objects.all()
    serializer_class = EmployeeDetailsSerializer
    # Corrected to a tuple for multiple fields
    lookup_fields = ('ee_id', 'case_id')

    def get_object(self):
        """
        Overriding `get_object` to fetch the instance based on multiple fields.
        """
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {field: self.kwargs[field]
                         for field in self.lookup_fields}
        obj = queryset.filter(**filter_kwargs).first()
        if not obj:
            raise Exception(f"Object not found with {filter_kwargs}")
        return obj

    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Logging the update action
            LogEntry.objects.create(
                action='Employee details updated',
                details=f'Employee details updated Successfully for Employee ID {instance.ee_id}'
            )

            # Preparing the response data
            response_data = {
                'success': True,
                'message': 'Data updated Successfully',
                'status_code': status.HTTP_200_OK
            }
            return JsonResponse(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse(
                {'error': str(
                    e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def get_employee_details(request):
    employees = employee_detail.objects.all()
    if employees.exists():
        try:
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except employee_detail.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_order_details(request):
    employees = garnishment_order.objects.all()
    if employees.exists():
        try:
            serializer = GarnishmentOrderSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except employee_detail.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        except Exception as e:
            return JsonResponse({'error': str(e), status: status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Company ID not found', 'status code': status.HTTP_404_NOT_FOUND})


@api_view(['GET'])
def get_single_employee_details(request, case_id, ee_id):
    employees = employee_detail.objects.filter(case_id=case_id, ee_id=ee_id)
    if employees.exists():
        try:
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except employee_detail.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})

# Get Employer Details from employer ID


@api_view(['GET'])
def get_employer_details(request, id):
    employees = Employer_Profile.objects.filter(id=id)
    if employees.exists():
        try:
            serializer = GetEmployerDetailsSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK}
            response_data['data'] = serializer.data
            return JsonResponse(response_data)
        except Employer_Profile.DoesNotExist:
            return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
    else:
        return JsonResponse({'message': 'Employer ID not found', 'status code': status.HTTP_404_NOT_FOUND})


@csrf_exempt
def insert_iwo_detail(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cid = data.get('cid')
            ee_id = data.get('ee_id')
            IWO_Status = data.get('IWO_Status')

            # Validate required fields
            if cid is None or ee_id is None or IWO_Status is None:
                return JsonResponse({'error': 'Missing required fields', 'code': status.HTTP_400_BAD_REQUEST})

            # Create a new IWO_Details_PDF instance and save it to the database
            iwo_detail = IWO_Details_PDF(
                cid=cid,
                ee_id=ee_id,
                IWO_Status=IWO_Status
            )
            iwo_detail.save()
            return JsonResponse({'message': 'IWO detail inserted Successfully', 'code': status.HTTP_201_CREATED})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON', 'status_code': status.HTTP_400_BAD_REQUEST})
        except Exception as e:
            return JsonResponse({'error': str(e), 'status code': status.HTTP_500_INTERNAL_SERVER_ERROR})

    return JsonResponse({'error': 'Invalid request method', 'status code': status.HTTP_405_METHOD_NOT_ALLOWED})


@csrf_exempt
def get_dashboard_data(request):
    try:
        total_iwo = IWO_Details_PDF.objects.count()

        employees_with_single_iwo = IWO_Details_PDF.objects.values(
            'cid').annotate(iwo_count=Count('cid')).filter(iwo_count=1).count()

        employees_with_multiple_iwo = IWO_Details_PDF.objects.values(
            'cid').annotate(iwo_count=Count('cid')).filter(iwo_count__gt=1).count()

        active_employees = IWO_Details_PDF.objects.filter(
            IWO_Status='active').count()

        data = {
            'Total_IWO': total_iwo,
            'Employees_with_Single_IWO': employees_with_single_iwo,
            'Employees_with_Multiple_IWO': employees_with_multiple_iwo,
            'Active_employees': active_employees,
        }
    except Exception as e:
        return JsonResponse({'error': str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})
    response_data = {
        'success': True,
        'message': 'Data Get Successfully',
        'status code': status.HTTP_200_OK,
        'data': data}
    return JsonResponse(response_data)


# For  Deleting the Employee Details
@method_decorator(csrf_exempt, name='dispatch')
class EmployeeDeleteAPIView(DestroyAPIView):

    queryset = employee_detail.objects.all()

    def get_object(self):
        ee_id = self.kwargs.get('ee_id')
        case_id = self.kwargs.get('case_id')

        try:
            return employee_detail.objects.get(ee_id=ee_id, case_id=case_id)
        except employee_detail.DoesNotExist:
            return None  # Return None instead of raising an exception

    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return JsonResponse(
                {'success': False, 'message': 'Employee record not found',
                    'status_code': status.HTTP_404_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        self.perform_destroy(instance)
        LogEntry.objects.create(
            action='Employee details Deleted',
            details=f'Employee details Deleted Successfully with Employee ID {kwargs.get("ee_id")} and Case ID {kwargs.get("case_id")}'
        )
        return JsonResponse(
            {'success': True, 'message': 'Employee Data Deleted Successfully',
                'status_code': status.HTTP_200_OK},
            status=status.HTTP_200_OK
        )


# For Deleting the Location Details
@method_decorator(csrf_exempt, name='dispatch')
class GarOrderDeleteAPIView(DestroyAPIView):
    queryset = garnishment_order.objects.all()
    lookup_field = 'case_id'

    @csrf_exempt
    def get_object(self):
        case_id = self.kwargs.get('case_id')
        return self.queryset.filter(case_id=case_id)

    @csrf_exempt
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        LogEntry.objects.create(
            action='Garnishment order details Deleted',
            details=f'Garnishment order deleted Successfully with Case ID'
        )
        response_data = {
            'success': True,
            'message': 'Garnishment order Data Deleted Successfully',
            'status code': status.HTTP_200_OK
        }
        return JsonResponse(response_data)


@api_view(['GET'])
def export_employee_data(request):
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

        # Define headers - should match serializer fields
        header_fields = [
            'ee_id', 'social_security_number', 'age', 'gender', 'home_state', 'work_state',
            'case_id', 'pay_period', 'is_blind', 'marital_status', 'filing_status', 'spouse_age',
            'is_spouse_blind', 'number_of_exemptions', 'support_second_family',
            'number_of_student_default_loan', 'garnishment_fees_status', 'garnishment_fees_suspended_till'
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
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'employee_details_{datetime.today().strftime("%m-%d-%y")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse(
            {'detail': str(
                e), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def export_order_data(request):
    try:
        employees = garnishment_order.objects.all()
        if not employees.exists():
            return JsonResponse(
                {'detail': 'No garnishment orders found',
                    'status': status.HTTP_404_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GarnishmentOrderSerializer(employees, many=True)

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Garnishment Orders"

        # Header fields (must match serializer keys)
        header_fields = [
            "eeid", "fein", "case_id", "work_state", "type", "sdu",
            "start_date", "end_date", "amount", "arrear_greater_than_12_weeks",
            "arrear_amount", "record_updated"
        ]
        ws.append(header_fields)

        # Write data rows
        for order in serializer.data:
            row = [order.get(field, '') for field in header_fields]
            ws.append(row)

        # Save to in-memory buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        # Prepare response
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'garnishment_orders_{datetime.today().strftime("%m-%d-%y")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse(
            {'detail': str(
                e), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Import employee details using the Excel file
class EmployeeImportView(APIView):
    """This view handles the import of employee details from an Excel file."""

    def post(self, request):
        try:
            if 'file' not in request.FILES:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']
            file_name = file.name

            # Check the file extension
            if file_name.endswith('.csv'):
                df = pandas.read_csv(file)
            elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb', '.odf', '.ods', '.odt')):
                df = pandas.read_excel(file)
                print("df", df)
            else:
                return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)

            employees = []
            for _, row in df.iterrows():
                employee_data = {
                    'ee_id': row['ee_id'],
                    'case_id': row['case_id'],
                    'age': row['age'],
                    'social_security_number': row['social_security_number'],
                    'is_blind': row['is_blind'],
                    'home_state': row['home_state'],
                    'work_state': row['work_state'],
                    'gender': row['gender'],
                    'pay_period': row['pay_period'],
                    'number_of_exemptions': row['number_of_exemptions'],
                    'filing_status': row['filing_status'],
                    'marital_status': row['marital_status'],
                    'number_of_student_default_loan': row['number_of_student_default_loan'],
                    'support_second_family': row['support_second_family'],
                    'spouse_age': row['spouse_age'],
                    'is_spouse_blind': row['is_spouse_blind'],
                    'garnishment_fees_status': row['garnishment_fees_status'],
                    'garnishment_fees_suspended_till': row['garnishment_fees_suspended_till'],
                }

                serializer = EmployeeDetailsSerializer(data=employee_data)
                if serializer.is_valid():
                    employees.append(serializer.save())
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            LogEntry.objects.create(
                action='Employee details Imported',
                details='Employee details Imported Successfully using excel file'
            )
        except Exception as e:
            return JsonResponse({'error': str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})

        return Response({"message": "File processed Successfully", "status code": status.HTTP_201_CREATED})


class GarnishmentOrderImportView(APIView):
    """This view handles the import of garnishment orders from a file."""

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
                return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."},
                                status=status.HTTP_400_BAD_REQUEST)

            orders = []
            for _, row in df.iterrows():
                order_data = {
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "amount": row["amount"],
                    "arrear_greater_than_12_weeks": row["arrear_greater_than_12_weeks"],
                    "arrear_amount": row["arrear_amount"],
                    "record_updated": row["record_updated"],
                    "case_id": row["case_id"],
                    "work_state": row["work_state"],
                    "type": row["type"],
                    "sdu": row["sdu"],
                    "eeid": row["eeid"],
                    "fein": row["fein"]
                }

                serializer = GarnishmentOrderSerializer(data=order_data)
                if serializer.is_valid():
                    orders.append(serializer.save())
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            LogEntry.objects.create(
                action='Garnishment Orders Imported',
                details='Garnishment orders imported Successfully using file.'
            )

        except Exception as e:
            return JsonResponse({'error': str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})

        return Response({"message": "File processed Successfully", "status code": status.HTTP_201_CREATED})


# Extracting the Last Five record from the Log Table
class LastFiveLogsView(APIView):
    def get(self, request, format=None):
        try:
            logs = LogEntry.objects.order_by('-timestamp')[:5]
            serializer = LogSerializer(logs, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK,
                'data': serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})


# Extracting the ALL Employer Detials
class EmployerProfileList(APIView):
    def get(self, request, format=None):
        try:
            employees = Employer_Profile.objects.all()
            serializer = EmployerProfileSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data retrieved Successfully',
                'status_code': status.HTTP_200_OK,
                'data': serializer.data
            }
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR})


# Extracting the ALL Employee Details
class EmployeeDetailsList(APIView):
    def get(self, request, format=None):
        try:
            employees = employee_detail.objects.all()
            serializer = EmployeeDetailsSerializer(employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK,
                'data': serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return Response({"error": str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})


class GETGarnishmentFeesStatesRule(APIView):
    def get(self, request, format=None):
        try:
            employees = garnishment_fees_states_rule.objects.all()
            serializer = GarnishmentFeesStatesRuleSerializer(
                employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK,
                'data': serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class GarFeesRulesUpdateAPIView(APIView):
    def put(self, request, rule):
        try:
            # Get the object to update
            employees = garnishment_fees_rules.objects.filter(rule=rule)

            if not employees.exists():
                return Response(
                    {
                        "success": False,
                        "message": "No records found for the given rule",
                        "status_code": status.HTTP_404_NOT_FOUND,
                    }
                )

            # Use first() to get the single instance
            serializer = GarnishmentFeesRulesSerializer(
                employees.first(), data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": "Data updated Successfully",
                        "status_code": status.HTTP_200_OK
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(['GET'])
def GETGarnishmentFeesRules(request, rule):
    employees = garnishment_fees_rules.objects.filter(rule=rule)

    if employees.exists():
        try:
            serializer = GarnishmentFeesRulesSerializer(
                employees, many=True)
            response_data = {
                'success': True,
                'message': 'Data Get Successfully',
                'status code': status.HTTP_200_OK,
                'data': serializer.data}
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        return JsonResponse({'message': 'Rule not found', 'status code': status.HTTP_404_NOT_FOUND})


class GarnishmentFeesRulesByState(APIView):
    def get(self, request, state):
        state = state.lower()
        employees = garnishment_fees_states_rule.objects.filter(state=state)

        if employees.exists():
            try:
                serializer = GarnishmentFeesStatesRuleSerializer(
                    employees, many=True)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved Successfully',
                    'status_code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data, status=status.HTTP_200_OK, safe=False)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while processing your request',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse({
            'success': False,
            'message': 'Rule not found',
            'status_code': status.HTTP_404_NOT_FOUND
        }, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = Employer_Profile.objects.get(email=email)
        except Employer_Profile.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        token = RefreshToken.for_user(user).access_token
        # Change this URL to point to your frontend
        reset_url = f'https://garnishment-react-main.vercel.app/reset-password/{str(token)}'
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_url}',
            'your-email@example.com',
            [email],
        )
        return Response({"message": "Password reset link sent.", "status code": status.HTTP_200_OK})


class PasswordResetConfirmView(APIView):
    def post(self, request, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['password']
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = Employer_Profile.objects.get(employer_id=user_id)
            user.set_password(new_password)
            user.save()
            employee = get_object_or_404(
                Employer_Profile, employer_name=user.employer_name, id=user.id)
        except (Employer_Profile.DoesNotExist, TokenError) as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})
        return Response({"message": "Password reset successful.", "status code": status.HTTP_200_OK})


@csrf_exempt
def SettingPostAPI(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['modes', 'visibilitys', 'employer_id']
            missing_fields = [
                field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return JsonResponse({'error': f'Required fields are missing: {", ".join(missing_fields)}', 'status_code': status.HTTP_400_BAD_REQUEST})

            user = setting.objects.create(**data)
            LogEntry.objects.create(
                action='setting details added',
                details=f'setting details added Successfully'
            )
            return JsonResponse({'message': 'Setting Details Successfully Registered', "status code": status.HTTP_201_CREATED})
        except Exception as e:
            return JsonResponse({'error': str(e), "status code": status.HTTP_500_INTERNAL_SERVER_ERROR})
    else:
        return JsonResponse({'message': 'Please use POST method', 'status code': status.HTTP_400_BAD_REQUEST})


class GETSettingDetails(APIView):
    def get(self, request, employer_id):
        employees = setting.objects.filter(employer_id=employer_id)
        if employees.exists():
            try:
                employee = employees.first()
                serializer = SettingSerializer(employee)
                response_data = {
                    'success': True,
                    'message': 'Data retrieved Successfully',
                    'status code': status.HTTP_200_OK,
                    'data': serializer.data
                }
                return JsonResponse(response_data)
            except setting.DoesNotExist:
                return JsonResponse({'message': 'Data not found', 'status code': status.HTTP_404_NOT_FOUND})
        else:
            return JsonResponse({'message': 'Employee ID not found', 'status code': status.HTTP_404_NOT_FOUND})


class APICallCountView(APIView):
    def get(self, request):
        logs = APICallLog.objects.values('date', 'endpoint', 'count')
        return Response(logs)

    def get(self, request):
        record = {
            "ee_id": "EE005114",
            "gross_pay": 1000.0,
            "state": "alaska",
            "no_of_exemption_for_self": 2,
            "pay_period": "Weekly",
            "filing_status": "single_filing_status",
            "net_pay": 858.8,
            "payroll_taxes": [
                {
                    "federal_income_tax": 80.0
                },
                {
                    "social_security_tax": 49.6
                },
                {
                    "medicare_tax": 11.6
                },
                {
                    "state_tax": 0.0
                },
                {
                    "local_tax": 0.0
                }
            ],
            "payroll_deductions": {
                "medical_insurance": 0.0
            },
            "age": 50,
            "is_blind": True,
            "is_spouse_blind": True,
            "spouse_age": 39,
            "support_second_family": "Yes",
            "no_of_student_default_loan": 2,
            "arrears_greater_than_12_weeks": "No",
            "garnishment_data": [
                {
                    "type": "child_support",
                    "data": [
                            {
                                "case_id": "C13278",
                                "amount": 200.0,
                                "arrear": 0
                            }
                    ]
                }
            ]
        }

        state = record.get("state").lower()
        gar_type = record.get("garnishment_data")[0]
        type = gar_type.get('type').lower()
        pay_period = record.get('pay_period').lower()
        data = garnishment_fees.objects.all()
        serializer = GarnishmentFeesSerializer(data, many=True)

        for item in serializer.data:
            if (item["state"].strip().lower() == state.strip().lower() and
                item["pay_period"].strip().lower() == pay_period.strip().lower() and
                    item["type"].strip().lower() == type.strip().lower()):
                return Response(item["amount"])

        # print("data",data)

        # return Response({"data":data})


# Upsert the company details
class UpsertEmployeeDataView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
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
                row = {k: v for k, v in row.items(
                ) if k and not k.startswith('Unnamed')}
                row = {
                    k: ("" if (k == "social_security_number" and isinstance(
                        v, float) and math.isnan(v)) else v)
                    for k, v in row.items()
                }

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
                                "%Y-%m-%d")
                    except Exception:
                        row["garnishment_fees_suspended_till"] = None

                case_id = row.get("case_id")
                ee_id = row.get("ee_id")
                if not ee_id or not case_id:
                    continue  # Skip if identifiers are missing

                boolean_fields = ['is_blind',
                                  'is_spouse_blind', 'support_second_family']
                for bfield in boolean_fields:
                    val = row.get(bfield)
                    if isinstance(val, str):
                        row[bfield] = val.lower() in ['true', '1', 'yes']

                obj = employee_detail.objects.filter(
                    case_id=case_id, ee_id=ee_id)

                if obj:
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
                    'message': 'Employee(s) imported Successfully',
                    'added_employees': added_employees
                })
            if updated_employees:
                response_data.append({
                    'message': 'Employee details updated Successfully',
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
            return Response({
                'success': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UpsertGarnishmentOrderView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if file.name.endswith('.csv'):
                data = list(csv.DictReader(
                    file.read().decode('utf-8').splitlines()))
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
                data = df.to_dict(orient='records')
            else:
                return Response({'error': 'Unsupported file format. Use CSV or Excel.'}, status=status.HTTP_400_BAD_REQUEST)

            added_orders, updated_orders = [], []

            for row in data:
                row = {k: v for k, v in row.items() if k and not str(
                    k).startswith('Unnamed')}

                # Format date fields if any
                for field in ['start_date', 'end_date', 'record_updated']:
                    value = row.get(field)
                    if value:
                        try:
                            if isinstance(value, datetime):
                                row[field] = value.strftime('%Y-%m-%d')
                            else:
                                parsed_date = pd.to_datetime(value)
                                row[field] = parsed_date.strftime('%Y-%m-%d')
                        except Exception:
                            row[field] = None

                case_id = row.get("case_id")
                if not case_id:
                    # Skip row if unique identifiers are missing
                    continue

                obj = garnishment_order.objects.filter(case_id=case_id).first()

                if obj:
                    has_changes = any(
                        str(getattr(obj, field, '')).strip() != str(
                            row.get(field, '')).strip()
                        for field in row.keys()
                        if hasattr(obj, field)
                    )
                    if has_changes:
                        serializer = GarnishmentOrderSerializer(
                            obj, data=row, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            updated_orders.append(case_id)
                else:
                    serializer = GarnishmentOrderSerializer(data=row)
                    if serializer.is_valid():
                        serializer.save()
                        added_orders.append(case_id)

            response_data = []
            if added_orders:
                response_data.append({
                    'message': 'Garnishment order(s) added Successfully',
                    'added_orders': added_orders
                })
            if updated_orders:
                response_data.append({
                    'message': 'Garnishment order(s) updated Successfully',
                    'updated_orders': updated_orders
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
            return Response({
                'success': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class Employeegarnishment_orderMatch_details(APIView):

    def get(self, request):
        employees = employee_detail.objects.all()
        garnishments = garnishment_order.objects.all()
        fees = garnishment_fees.objects.all()

        # if not employees.exists() or not garnishments.exists() or not fees.exists():
        #     return Response({"message": "No data available"}, status=status.HTTP_204_NO_CONTENT)

        df_employees = pd.DataFrame(list(employees.values()))
        df_garnishments = pd.DataFrame(list(garnishments.values()))
        df_fees = pd.DataFrame(list(fees.values()))

        if df_employees.empty or df_garnishments.empty or df_fees.empty:
            return Response({"message": "No matching data found"}, status=status.HTTP_204_NO_CONTENT)

        required_columns_employees = {'ee_id', 'work_state', 'pay_period'}
        required_columns_garnishments = {'eeid', 'type'}
        required_columns_fees = {'state', 'type', 'pay_period', 'rules'}

        if not required_columns_employees.issubset(df_employees.columns) or \
           not required_columns_garnishments.issubset(df_garnishments.columns) or \
           not required_columns_fees.issubset(df_fees.columns):
            return Response({"message": "Missing required columns"}, status=status.HTTP_400_BAD_REQUEST)

        df_employees['work_state'] = df_employees['work_state'].str.strip(
        ).str.lower()
        df_employees['pay_period'] = df_employees['pay_period'].astype(
            str).str.strip().str.lower()

        df_garnishments['type'] = df_garnishments['type'].str.strip(
        ).str.lower()
        df_garnishments['eeid'] = df_garnishments['eeid'].astype(
            str).str.strip()

        df_fees['state'] = df_fees['state'].str.strip().str.lower()
        df_fees['type'] = df_fees['type'].str.strip().str.lower()
        df_fees['pay_period'] = df_fees['pay_period'].astype(
            str).str.strip().str.lower()

        merged_df = df_employees.merge(
            df_garnishments[['eeid', 'case_id', 'type']],
            left_on=['ee_id', 'case_id'],
            right_on=['eeid', 'case_id'],
            how='left'
        ).drop(columns=['eeid'])

        final_df = merged_df.merge(
            df_fees[['state', 'type', 'pay_period', 'rules']],
            left_on=['work_state', 'type', 'pay_period'],
            right_on=['state', 'type', 'pay_period'],
            how='left'
        ).drop(columns=['state'])

        print()

        data = final_df.where(pd.notna(final_df),
                              None).to_dict(orient='records')

        response_data = {
            'success': True,
            'message': 'Data Get Successfully',
            'status_code': status.HTTP_200_OK,
            "data": data

        }
        return Response(response_data, status=status.HTTP_200_OK)


def replace_nan_with_none(obj):
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(item) for item in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or pd.isna(obj)):
        return None
    elif pd.isna(obj):
        return None
    else:
        return obj


class convert_excel_to_json(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        try:

            if not file:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Read the Excel sheets
            garnishment_order_details = pd.read_excel(
                file, sheet_name='Garnishment Order')
            # lowercase
            garnishment_order_details.columns = garnishment_order_details.columns.str.strip().str.lower()
            payroll_batch_details = pd.read_excel(
                file, sheet_name='Payroll Batch', header=[0, 1])
            # Convert multi-index columns to single-level
            payroll_batch_details.columns = payroll_batch_details.columns.map(
                lambda x: '_'.join(str(i)
                                   for i in x) if isinstance(x, tuple) else x
            ).str.lower()
            # Strip spaces from column names
            payroll_batch_details.columns = payroll_batch_details.columns.str.strip()
# OLD
            # # Rename columns properly
            # column_mapping = {
            #     'Unnamed: 1_level_0_EEID': 'ee_id',
            #     'Unnamed: 0_level_0_CaseID' :"case_id",
            #     'Unnamed: 2_level_0_PayPeriod': 'pay_period',
            #     'Earnings_Gross Pay': 'gross_pay',
            #     'Earnings_Wages': 'wages',
            #     'Earnings_Commission+Bonus': 'commission_and_bonus',
            #     'Earnings_Non Accountable Allowances': 'non_accountable_allowances',
            #     'Taxes_FederalIncomeTax': 'federal_income_tax',
            #     'Taxes_StateTax': 'state_tax',
            #     'Taxes_LocalTax': 'local_tax',
            #     'Taxes_MedicareTax': 'medicare_tax',
            #     'Taxes_SocialSecurityTax': 'social_security_tax',
            #     'Deductions_MedicalInsurance': 'medical_insurance',
            #     "Deductions_FamliTax" : "famli_tax",
            #     'Deductions_NetPay': 'net_pay'
            # }
# NEW MAP    PIN START
            column_mapping = {
                'unnamed: 1_level_0_eeid': 'ee_id',
                'unnamed: 1_level_0_ee id': 'ee_id',

                'unnamed: 0_level_0_caseid': "case_id",
                'unnamed: 0_level_0_case id': "case_id",

                'unnamed: 2_level_0_payperiod': 'pay_period',
                'unnamed: 2_level_0_pay period': 'pay_period',

                'earnings_gross pay': 'gross_pay',
                'earnings_gross pay': 'gross_pay',

                'earnings_wages': 'wages',
                'earnings_wages': 'wages',
                # new field
                'earnings_commission': 'commission',
                'earnings_bonus': 'bonus',

                'earnings_commission+bonus': 'commission_and_bonus',
                'earnings_commission & bonus': 'commission_and_bonus',

                'earnings_non accountable allowances': 'non_accountable_allowances',
                'earnings_non accountable allowances': 'non_accountable_allowances',

                'taxes_federalincometax': 'federal_income_tax',
                'taxes_fed tax amt': 'federal_income_tax',

                'taxes_statetax': 'state_tax',
                'taxes_state tax amt': 'state_tax',

                'taxes_localtax': 'local_tax',
                'taxes_local / other taxes': 'local_tax',

                'taxes_medicaretax': 'medicare_tax',
                'taxes_med tax': 'medicare_tax',

                'taxes_socialsecuritytax': 'social_security_tax',
                'taxes_oasdi tax': 'social_security_tax',


                'deductions_medicalinsurancepretax': 'medical_insurance',
                'deductions_medical insurance': 'medical_insurance',

                # not found
                "Deductions_FamliTax": "famli_tax",
                # NEWLY ADDED
                "deductions_californiasdi": "california_sdi",
                'deductions_sdi': "california_sdi",

                "deductions_life insurance": "life_insurance",
                'deductions_life insurance': "life_insurance",

                "deductions_industrial insurance": "industrial_insurance",
                'deductions_industrial insurance': "industrial_insurance",

                "taxes_wilmingtontax": "wilmington_tax",
                'taxes_wilmington tax': "wilmington_tax",

                "deductions_uniondues": "union_dues",
                'deductions_union dues': "union_dues",

                # famli_tax NOT PRESENT
                'deductions_netpay': 'net_pay',
                'deductions_net pay': 'net_pay',

            }
# NEW MAP    PIN END
            payroll_batch_details.rename(columns=column_mapping, inplace=True)
            # print("payroll_batch_detailsqqqqqqq",payroll_batch_details.columns)
# previous mapping
            # # Rename columns in garnishment_order_de
            # column_mapping_garnishment = {
            #     'EEID': 'ee_id',
            #     'CaseID': 'case_id',
            #     'FEIN': 'fein',
            #     'IsBlind': 'is_blind',
            #     'Age': 'age',
            #     'FilingStatus': 'filing_status',
            #     'SupportSecondFamily': 'support_second_family',
            #     'SpouseAge ': 'spouse_age',
            #     'IsSpouseBlind': 'is_spouse_blind',
            #     'OrderedAmount': 'ordered_amount',
            #     'ArrearsGreaterThan12Weeks': 'arrears_greater_than_12_weeks',
            #     'TotalExemptions': 'no_of_exemption_including_self',
            #     'WorkState': 'state',
            #     'HomeState': 'home_state',
            #     'NumberofStudentLoan': 'no_of_student_default_loan',
            #     'No.OFExemptionIncludingSelf': 'no_of_exemption_including_self',
            #     "Type": "garnishment_type",
            #     "ArrearAmount": "arrear_amount",
            #     "CurrentMedicalSupport": "current_medical_support",
            #     "Past-Due MedicalSupport": "past_due_medical_support",
            #     "CurrentSpousalSupport": "current_spousal_support",
            #     "Past-DueSpousalSupport": "past_due_spousal_support"
            # }
# NEW STA    R
            column_mapping_garnishment = {
                'eeid': 'ee_id',
                'ee id': 'ee_id',

                'caseid': 'case_id',
                'case id': 'case_id',

                # 'fein': 'fein', #same
                # 'IsBlind': 'is_blind',
                # 'BLIND: 'is_blind',
                # 'Age': 'age', #same
                'filingstatus': 'filing_status',
                'filing status': 'filing_status',

                'supportsecondfamily': 'support_second_family',
                'supports 2nd fam': 'support_second_family',

                # spouseage ': 'spouse_age',

                # isspouseblind': 'is_spouse_blind',

                'orderedamount': 'ordered_amount',
                'order $': 'ordered_amount',

                'arrearsgreaterthan12weeks': 'arrears_greater_than_12_weeks',  # not present
                'arrear > 12 weeks': 'arrears_greater_than_12_weeks',

                # 'TotalExemptions': 'no_of_exemption_including_self', #not present
                'workstate': 'state',  # not present
                'work state': 'state',

                'homestate': 'home_state',  # not present
                'home state': 'home_state',

                # 'NumberofStudentLoan': 'no_of_student_default_loan',  #not present
                'no. of exemptions including self': 'no_of_exemption_including_self',  # not present

                "type": "garnishment_type",
                'garn type': "garnishment_type",

                "arrearamount": "arrear_amount",
                'arrear amount': "arrear_amount",

                # in new sheet
                'no. of dependent child': 'no_of_dependent_child'

                # "currentmedicalsupport": "current_medical_support",
                # "past-due medicalsupport": "past_due_medical_support",
                # "currentspousalsupport": "current_spousal_support",
                # "past-duespousalsupport": "past_due_spousal_support"
            }

            garnishment_order_details = garnishment_order_details.dropna(
                axis=1, how='all')
            # print("columns_garnishment", garnishment_order_details.columns)
            payroll_batch_details = payroll_batch_details.dropna(
                axis=1, how='all')
            garnishment_order_details.rename(
                columns=column_mapping_garnishment, inplace=True)
            # print("garnishment__c", garnishment_order_details.columns)

            # pd.set_option('future.no_silent_downcasting', True)
            # print('garnishment_order_details', garnishment_order_details.columns)
            garnishment_order_details['case_id'] = garnishment_order_details['case_id'].str.strip(
            )
            payroll_batch_details['case_id'] = payroll_batch_details['case_id'].str.strip(
            )
            concatenated_df = pd.merge(
                garnishment_order_details, payroll_batch_details, on='case_id')
            concatenated_df = concatenated_df.loc[:, ~concatenated_df.columns.duplicated(
                keep='first')]
            # print('concatenated_df', concatenated_df)
            # Data transformations
            if 'filing_status' in concatenated_df.columns and concatenated_df['filing_status'].notna().any():
                concatenated_df['filing_status'] = concatenated_df['filing_status'].str.lower(
                ).str.replace(' ', '_')
            else:
                concatenated_df['filing_status'] = None

            concatenated_df['batch_id'] = "B001A"
            concatenated_df['arrears_greater_than_12_weeks'] = concatenated_df['arrears_greater_than_12_weeks'].astype(bool).apply(
                lambda x: "Yes" if x == True or x == 1 else "No" if x == False or x == 0 else x)
            concatenated_df['support_second_family'] = concatenated_df['support_second_family'].astype(bool).apply(
                lambda x: "Yes" if x == True or x == 1 or str(x).lower() == "true" or x == "TRUE" else "No" if x == False or x == 0 or str(x).lower() == "false" or x == "FALSE" else x)

            concatenated_df['garnishment_type'] = concatenated_df['garnishment_type'].replace(
                {'Student Loan': "student default loan"}
            )

            # print("concatenated_df", concatenated_df.columns)
            # Generate batch ID
            # Using last 3 digits of timestamp to ensure uniqueness
            number = int(time.time() % 1000)
            letter = random.choice(string.ascii_uppercase)
            batch_id = f"B{number:03d}{letter}"

            output_json = {"batch_id": batch_id, "cases": []}
            # Group by employee ID
            for ee_id, group in concatenated_df.groupby("ee_id_x"):
                # Take the first row for general employee de
                first_row = group.iloc[0]
                # Create garnishment data list
                garnishment_data = {
                    "type": first_row["garnishment_type"],
                    "data": []}

                # Iterate over cases for the same employee
                for _, row in group.iterrows():
                    garnishment_data["data"].append({
                        "case_id": row.get("case_id", None),
                        "ordered_amount": row["ordered_amount"],
                        "arrear_amount": row["arrear_amount"],
                        # "current_medical_support": row.get("current_medical_support",0),
                        # "past_due_medical_support": row.get("past_due_medical_support",0),
                        # "current_spousal_support": row.get("current_spousal_support",0),
                        # "past_due_spousal_support": row.get("past_due_spousal_support",0)
                    }
                    )
                # Append the consolidated employee data
                output_json["cases"].append({
                    "ee_id": row["ee_id_x"],
                    "work_state": row.get("state").strip(),
                    "no_of_exemption_including_self": row.get("no_of_exemption_including_self", None),
                    "pay_period": row["pay_period"],
                    "filing_status": row["filing_status"],
                    "wages": row.get("wages", 0),
                    "commission_and_bonus": row.get("commission_and_bonus", 0),
                    "non_accountable_allowances": row.get("non_accountable_allowances", 0),
                    "gross_pay": row.get("gross_pay", 0),
                    "payroll_taxes": {
                        "federal_income_tax": row.get("federal_income_tax", 0),
                        "social_security_tax": row.get("social_security_tax", 0),
                        "medicare_tax": row.get("medicare_tax", 0),
                        "state_tax": row.get("state_tax", 0),
                        "local_tax": row.get("local_tax", 0),
                        "union_dues": row.get("union_dues", 0),  # NEWLY
                        # NEWLY
                        "wilmington_tax": row.get("wilmington_tax", 0),
                        # NEWLY
                        "medical_insurance": row.get("medical_insurance", 0),
                        # NEWLY
                        "industrial_insurance": row.get("industrial_insurance", 0),
                        # NEWLY
                        "life_insurance": row.get("life_insurance", 0),
                        # NEWLY
                        "california_sdi": row.get("california_sdi", 0),
                        "famli_tax": row.get("famli_tax", 0)
                    },
                    "net_pay": row.get("net_pay"),
                    # "age": row.get("age",None),
                    # "is_blind": row.get("is_blind",None),
                    # "is_spouse_blind": row.get("is_spouse_blind",None),
                    # "spouse_age": row.get("spouse_age",None),
                    "support_second_family": row["support_second_family"],
                    "no_of_dependent_child": row.get("no_of_dependent_child", 0),
                    # "no_of_student_default_loan": row.get("no_of_student_default_loan",0),
                    "arrears_greater_than_12_weeks": row["arrears_greater_than_12_weeks"],
                    "garnishment_data": [garnishment_data]
                })
            output_json = replace_nan_with_none(output_json)
            return JsonResponse(output_json, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR})


class GarCalculationRules(APIView):
    """Get the withholding limit rule data for a specific state."""

    def get(self, request, state, employee_id, supports_2nd_family, arrears_of_more_than_12_weeks, de, no_of_order):
        try:

            state = gc.StateAbbreviations(state).get_state_name_and_abbr()
            file_path = os.path.join(
                settings.BASE_DIR,
                'User_app',
                'configuration files/child support tables/withholding_rules.json'
            )
            # Reading the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Accessing child support data
            ccpa_rules_data = data.get("WithholdingRules", [])

            # Searching for the matching state
            records = next(
                (rec for rec in ccpa_rules_data if rec['state'].lower() == state.lower()), None)

            de_gt_145 = "No" if float(
                de) <= 145 or records["rule"] != "Rule_6" else "Yes"

            # Determine arrears_of_more_than_12_weeks
            arrears_of_more_than_12_weeks = "" if records[
                "rule"] == "Rule_4" else arrears_of_more_than_12_weeks

            # Determine order_gt_one
            order_gt_one = "No" if int(
                no_of_order) > 1 or records["rule"] != "Rule_4" else "Yes"

            # Identify withholding limit using state rules
            wl_limit = gc.WLIdentifier().find_wl_value(state, employee_id, supports_2nd_family,
                                                       arrears_of_more_than_12_weeks, de_gt_145, order_gt_one)

            records["applied_withholding_limit"] = round(wl_limit*100, 0)

            record = ChildSupport(state).get_mapping_keys()
            result = {}

            for item in record:
                key = item.split("_")[0]
                result[key] = item

            records["mandatory_deductions"] = result
            # Determine if DE > 145 and if there is more than one order

            if record:
                response_data = {
                    'success': True,
                    'message': 'Data retrieved Successfully',
                    'status_code': status.HTTP_200_OK,
                    'data': records
                }
                return Response(response_data, status=status.HTTP_200_OK)

            return Response({
                'success': False,
                'message': 'State not found',
                'status_code': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "error": str(e),
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_single_file(file):
    try:
        file_bytes = file.read()  # This MUST be bytes, not a URL or string
        endpoint = os.getenv("AZURE_ENDPOINT")
        key = os.getenv("AZURE_KEY")
        # Optional: store file to Vercel Blob for later download/viewing
        blob_info = put(f"PDFFiles/{file.name}", file_bytes)
        blob_url = blob_info["url"]

        obj = IWOPDFFiles.objects.create(name=file.name, pdf_url=blob_url)
        serializer = IWOPDFFilesSerializer(obj)

        # Analyze file content (file_bytes, not URL)
        document_analysis_client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        poller = document_analysis_client.begin_analyze_document(
            model_id="from_data", document=file_bytes)
        result = poller.result()

        documents_data = []
        for idx, doc in enumerate(result.documents):
            fields = {
                field_name: (field.value if field.value else 0)
                for field_name, field in doc.fields.items()
            }
            fields["id"] = obj.id
            documents_data.append({
                "fields": fields
            })

        # Save to DB (adjust as needed)
        extracted_data = withholding_order_data.objects.create(
            **documents_data[0]["fields"])

        return serializer.data

    except Exception as e:
        return {
            'success': False,
            'message': 'Error occurred while uploading the file',
            'status_code': status.HTTP_200_OK,
            'data': None,
            "error": str(e)
        }


class PDFUploadView(APIView):
    def post(self, request):
        try:
            files = request.FILES.getlist("file")

            if not files:
                return Response({"error": "No files provided"}, status=400)

            results = list((handle_single_file, files))
            print("results", results)

            return Response({
                'success': True,
                "message": "IWO PDF Files Successfully uploaded",
                "status_code": status.HTTP_201_CREATED,
                "results": results
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error occurred while uploading the file',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GETIWOPDFData(APIView):
    def get(self, request, *args, **kwargs):
        try:
            ids_param = request.query_params.get('ids')
            ids = ids_param.split(',')
            files = withholding_order_data.objects.filter(id__in=ids)
            serializer = WithholdingOrderDataSerializers(files, many=True)
            response_data = {
                'success': True,
                'message': 'Data retrieved Successfully',
                'status_code': status.HTTP_200_OK,
                'data': serializer.data
            }
            return Response(response_data)
        except Exception as e:
            response_data = {
                'success': False,
                'message': 'Data retrieved failed',
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }
            return Response(response_data)


# APIView for State Tax Levy Rules
class StateTaxLevyConfigAPIView(APIView):

    def get(self, request, state=None):
        try:
            if state:
                state = gc.StateAbbreviations(
                    state.strip()).get_state_name_and_abbr().title()
                try:
                    rule = state_tax_levy_rule.objects.get(state=state)
                    serializer = StateTaxLevyConfigSerializers(rule)
                    return ResponseHelper.success_response(f'Data for state "{state}" fetched successfully', serializer.data)
                except state_tax_levy_rule.DoesNotExist:
                    return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
            else:
                rules = state_tax_levy_rule.objects.all()
                serializer = StateTaxLevyConfigSerializers(rules, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)

        except Exception as e:
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = StateTaxLevyConfigSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, state=None):
        if not state:
            return ResponseHelper.error_response('State is required in URL to update data', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            state_tax_rule = state_tax_levy_rule.objects.get(state=state)
        except state_tax_levy_rule.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)

        try:
            serializer = StateTaxLevyConfigSerializers(
                state_tax_rule, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data updated successfully', serializer.data)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while updating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, state=None):
        if not state:
            return ResponseHelper.error_response('State is required in URL to delete data', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            state_tax_rule = state_tax_levy_rule.objects.get(state=state)
            state_tax_rule.delete()
            return ResponseHelper.success_response(f'Data for state "{state}" deleted successfully')
        except state_tax_levy_rule.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while deleting data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StateTaxLevyRuleAPIView(APIView):
    def get(self, request, case_id):
        try:
            rule = state_tax_levy_applied_rule.objects.get(case_id=case_id)
            serializer = StateTaxLevyRulesSerializers(rule)
            return ResponseHelper.success_response(f'Data for case_id "{case_id}" fetched successfully', serializer.data)
        except state_tax_levy_rule.DoesNotExist:
            return ResponseHelper.error_response(f'case_id "{case_id}" not found', status_code=status.HTTP_404_NOT_FOUND)


class StateTaxLevyRuleEditPermissionAPIView(APIView):
    def post(self, request):
        try:
            serializer = StateTaxLevyRuleEditPermissionSerializers(
                data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, state=None):
        try:
            if state:
                try:
                    state = gc.StateAbbreviations(
                        state.strip()).get_state_name_and_abbr().title()
                    rule = state_tax_levy_rule_edit_permission.objects.get(
                        state=state)
                    serializer = StateTaxLevyRuleEditPermissionSerializers(
                        rule)
                    return ResponseHelper.success_response(f'Data for state "{state}" fetched successfully', serializer.data)
                except state_tax_levy_rule_edit_permission.DoesNotExist:
                    return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
            else:
                rules = state_tax_levy_rule_edit_permission.objects.all()
                serializer = StateTaxLevyRuleEditPermissionSerializers(
                    rules, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)

        except Exception as e:
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
