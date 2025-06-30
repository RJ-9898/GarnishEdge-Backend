from django.http import JsonResponse, HttpResponse
from rest_framework import status
from django.http import JsonResponse
from vercel_blob import put
import numpy as np
from django.conf import settings
import datetime as dt
from openpyxl import Workbook
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from GarnishEdge_Project.garnishment_library.utility_class import ResponseHelper
from GarnishEdge_Project.garnishment_library.gar_resused_classes import StateAbbreviations, WLIdentifier
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
import os
from User_app.serializers import (GarnishmentOrderSerializer,
                                  LogSerializer, GarnishmentFeesRulesSerializer, IWOPDFFilesSerializer, WithholdingOrderDataSerializers)
from io import BytesIO
import logging
import time
import random
import string
import json
from rest_framework.response import Response
from django.http import HttpResponse
import csv
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
import pandas as pd
from django.http import JsonResponse
from datetime import datetime
from User_app.models import (garnishment_order,
                             IWO_Details_PDF, IWOPDFFiles, garnishment_fees_rules, LogEntry, withholding_order_data)
from drf_yasg import openapi
from GarnishEdge_Project.garnishment_library.child_support import ChildSupport
from drf_yasg.utils import swagger_auto_schema
from GarnishEdge_Project.garnishment_library.utility_class import ResponseHelper
from User_app.constants import (
    EmployeeFields as EE,
    GarnishmentTypeFields as GT,
    CalculationFields as CA,
    PayrollTaxesFields as PT,
    CalculationResponseFields as CR,
    ResponseMessages,
    BatchDetail
)
from django.http import JsonResponse

from User_app.exception_handler import log_and_handle_exceptions
logger = logging.getLogger(__name__)


class InsertIWODetailView(APIView):
    """
    API view to insert IWO (Income Withholding Order) detail records.
    Handles POST requests with robust validation and exception handling.
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cid': openapi.Schema(type=openapi.TYPE_STRING, description='Case ID'),
                EE.EMPLOYEE_ID: openapi.Schema(type=openapi.TYPE_STRING, description='Employee ID'),
                'IWO_Status': openapi.Schema(type=openapi.TYPE_STRING, description='IWO Status'),
            },
            required=['cid', EE.EMPLOYEE_ID, 'IWO_Status']
        ),
        responses={
            201: 'IWO detail inserted successfully',
            400: 'Missing required fields or invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        try:
            # Parse JSON body
            if isinstance(request.data, dict):
                data = request.data
            else:
                try:
                    data = json.loads(request.body)
                except Exception:
                    return Response(
                        {
                            'error': ResponseMessages.INVALID_GARNISHMENT_DATA,
                            'status_code': status.HTTP_400_BAD_REQUEST
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            cid = data.get('cid')
            ee_id = data.get(EE.EMPLOYEE_ID)
            IWO_Status = data.get('IWO_Status')

            # Validate required fields
            missing_fields = [field for field in [
                'cid', EE.EMPLOYEE_ID, 'IWO_Status'] if data.get(field) is None]
            if missing_fields:
                return Response(
                    {
                        'error': f"Missing required fields: {', '.join(missing_fields)}",
                        'status_code': status.HTTP_400_BAD_REQUEST
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create and save the IWO_Details_PDF instance
            iwo_detail = IWO_Details_PDF(
                cid=cid,
                ee_id=ee_id,
                IWO_Status=IWO_Status
            )
            iwo_detail.save()

            return Response(
                {
                    'message': 'IWO detail inserted successfully',
                    'status_code': status.HTTP_201_CREATED
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # logger.error(f"Error inserting IWO detail: {e}")
            return Response(
                {
                    'error': f"Internal server error: {str(e)}",
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Helper function to replace NaNs with None recursively


def clean_data_for_json(data):
    """
    Recursively convert NaN to None and NumPy types to native Python types
    so the structure is JSON serializable.
    """
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif pd.isna(data):
        return None
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    elif isinstance(data, (np.bool_, bool)):
        return bool(data)
    else:
        return data


class ConvertExcelToJsonView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="Excel file to upload"
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
            400: 'No file provided or missing key in data',
            422: 'Data value error',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Load Excel sheets
            garnishment_df = pd.read_excel(
                file, sheet_name='Garnishment Order')
            garnishment_df.columns = garnishment_df.columns.str.strip().str.lower()

            payroll_df = pd.read_excel(
                file, sheet_name='Payroll Batch', header=[0, 1])
            payroll_df.columns = payroll_df.columns.map(
                lambda x: '_'.join(str(i)
                                   for i in x) if isinstance(x, tuple) else x
            ).str.lower().str.strip()

            # Define column mapping dictionaries
            payroll_column_map = {
                'unnamed: 1_level_0_eeid': EE.EMPLOYEE_ID,
                'unnamed: 0_level_0_caseid': EE.CASE_ID,
                'unnamed: 2_level_0_payperiod': EE.PAY_PERIOD,
                'unnamed: 3_level_0_payrolldate': EE.PAYROLL_DATE,
                'earnings_grosspay': CA.GROSS_PAY,
                'earnings_wages': CA.WAGES,
                'earnings_commission&bonus': CA.COMMISSION_AND_BONUS,
                'earnings_nonaccountableallowances': CA.NON_ACCOUNTABLE_ALLOWANCES,
                'taxes_fedtaxamt': PT.FEDERAL_INCOME_TAX,
                'taxes_statetaxamt': PT.STATE_TAX,
                'taxes_local/othertaxes': PT.LOCAL_TAX,
                'taxes_medtax': PT.MEDICARE_TAX,
                'taxes_oasditax': PT.SOCIAL_SECURITY_TAX,
                'deductions_medicalinsurance': PT.MEDICAL_INSURANCE_PRETAX,
                'deductions_sdi': PT.CALIFORNIA_SDI,
                'deductions_lifeinsurance': PT.LIFE_INSURANCE,
                'taxes_wilmingtontax': PT.WILMINGTON_TAX,
                'deductions_uniondues': PT.UNION_DUES,
                'deductions_netpay': CA.NET_PAY,
                'deductions_famlitax': PT.FAMLI_TAX,
                'deductions_industrialinsurance': PT.INDUSTRIAL_INSURANCE,
            }

            garnishment_column_map = {
                'eeid': EE.EMPLOYEE_ID, 'caseid': EE.CASE_ID, 'ssn': EE.SSN,
                'filingstatus': EE.FILING_STATUS,
                'supportsecondfamily': EE.SUPPORT_SECOND_FAMILY, 'supports2ndfam': EE.SUPPORT_SECOND_FAMILY,
                'orderedamount': CA.ORDERED_AMOUNT, 'ordered$': CA.ORDERED_AMOUNT,
                'arrear>12weeks': EE.ARREARS_GREATER_THAN_12_WEEKS,
                'arrears_greater_than_12_weeks': EE.ARREARS_GREATER_THAN_12_WEEKS,
                'workstate': EE.WORK_STATE,  'homestate': EE.HOME_STATE,
                'no.ofexemptionsincludingself': EE.NO_OF_EXEMPTION_INCLUDING_SELF, 'no.ofexemptionincludingself': EE.NO_OF_EXEMPTION_INCLUDING_SELF,
                'garntype': EE.GARNISHMENT_TYPE,
                'arrearamount': CA.ARREAR_AMOUNT, 'arrear$': CA.ARREAR_AMOUNT,
                'no. ofdependentchild(underthe ageof16)': EE.NO_OF_DEPENDENT_CHILD,
                'isblind': EE.IS_BLIND, 'age': EE.AGE, 'spouseage': EE.SPOUSE_AGE,
                'filingstatus': EE.FILING_STATUS, 'isspouseblind': EE.IS_SPOUSE_BLIND,
                'statementofexemptionreceiveddate': EE.STATEMENT_OF_EXEMPTION_RECEIVED_DATE,
                # 'debt type': EE.DEBT_TYPE,
                'garnstartdate': EE.GARN_START_DATE,
                'consumerdebt': EE.CONSUMER_DEBT, 'non-consumerdebt': EE.NON_CONSUMER_DEBT}

            # Drop empty columns and rename
            garnishment_df.dropna(axis=1, how='all', inplace=True)
            payroll_df.dropna(axis=1, how='all', inplace=True)

            garnishment_df.rename(columns=garnishment_column_map, inplace=True)
            payroll_df.rename(columns=payroll_column_map, inplace=True)

            # Strip 'case_id' fields before merging
            garnishment_df[EE.CASE_ID] = garnishment_df[EE.CASE_ID].str.strip()
            payroll_df[EE.CASE_ID] = payroll_df[EE.CASE_ID].str.strip()
            garnishment_df[EE.GARNISHMENT_TYPE] = garnishment_df[EE.GARNISHMENT_TYPE].str.strip(
            )

            # Formated "mm-dd-yyyy"
            date_cols = [
                'statement_of_exemption_received_date', 'garn_start_date']
            garnishment_df[date_cols] = garnishment_df[date_cols].apply(
                lambda col: col.dt.strftime('%m-%d-%Y'))

            merged_df = pd.merge(garnishment_df, payroll_df, on=EE.CASE_ID)
            merged_df = merged_df.loc[:, ~
                                      merged_df.columns.duplicated(keep='first')]

            # Clean specific columns
            if EE.FILING_STATUS in merged_df.columns and merged_df[EE.FILING_STATUS].notna().any():
                merged_df[EE.FILING_STATUS] = merged_df[EE.FILING_STATUS].str.lower(
                ).str.replace(" ", "_")
            else:
                merged_df[EE.FILING_STATUS] = None

            merged_df[EE.ARREARS_GREATER_THAN_12_WEEKS] = merged_df[EE.ARREARS_GREATER_THAN_12_WEEKS].astype(bool).apply(
                lambda x: "Yes" if x else "No"
            )

            merged_df[EE.SUPPORT_SECOND_FAMILY] = merged_df[EE.SUPPORT_SECOND_FAMILY].astype(bool).apply(
                lambda x: "Yes" if str(x).lower() in ['true', '1'] else "No"
            )

            merged_df[EE.GARNISHMENT_TYPE] = merged_df[EE.GARNISHMENT_TYPE].replace(
                {'Student Loan': GT.STUDENT_DEFAULT_LOAN}
            )

            # Generate dynamic batch ID
            batch_id = f"B{int(time.time() % 1000):03d}{random.choice(string.ascii_uppercase)}"

            # Build JSON structure
            output_json = {BatchDetail.BATCH_ID: batch_id, "cases": []}

            for ee_id, group in merged_df.groupby(f"{EE.EMPLOYEE_ID}_x"):
                first_row = group.iloc[0]

                garnishment_data = {
                    EE.GARNISHMENT_TYPE: first_row.get(EE.GARNISHMENT_TYPE),
                    "data": [
                        {
                            EE.CASE_ID: row.get(EE.CASE_ID),
                            CA.ORDERED_AMOUNT: row.get(CA.ORDERED_AMOUNT),
                            CA.ARREAR_AMOUNT: row.get(CA.ARREAR_AMOUNT)
                        }
                        for _, row in group.iterrows()
                    ]
                }

                output_json["cases"].append({
                    EE.EMPLOYEE_ID: ee_id,
                    EE.WORK_STATE: first_row.get(EE.WORK_STATE, "").strip(),
                    EE.NO_OF_EXEMPTION_INCLUDING_SELF: first_row.get(EE.NO_OF_EXEMPTION_INCLUDING_SELF),
                    EE.PAY_PERIOD: first_row.get(EE.PAY_PERIOD),
                    EE.FILING_STATUS: first_row.get(EE.FILING_STATUS),
                    CA.WAGES: first_row.get(CA.WAGES, 0),
                    CA.COMMISSION_AND_BONUS: first_row.get(CA.COMMISSION_AND_BONUS, 0),
                    CA.NON_ACCOUNTABLE_ALLOWANCES: first_row.get(CA.NON_ACCOUNTABLE_ALLOWANCES, 0),
                    CA.GROSS_PAY: first_row.get(CA.GROSS_PAY, 0),
                    PT.PAYROLL_TAXES: {
                        PT.FEDERAL_INCOME_TAX: first_row.get(PT.FEDERAL_INCOME_TAX, 0),
                        PT.SOCIAL_SECURITY_TAX: first_row.get(PT.SOCIAL_SECURITY_TAX, 0),
                        PT.MEDICARE_TAX: first_row.get(PT.MEDICARE_TAX, 0),
                        PT.STATE_TAX: first_row.get(PT.STATE_TAX, 0),
                        PT.LOCAL_TAX: first_row.get(PT.LOCAL_TAX, 0),
                        PT.UNION_DUES: first_row.get(PT.UNION_DUES, 0),
                        PT.WILMINGTON_TAX: first_row.get(PT.WILMINGTON_TAX, 0),
                        PT.MEDICAL_INSURANCE_PRETAX: first_row.get(PT.MEDICAL_INSURANCE_PRETAX, 0),
                        PT.INDUSTRIAL_INSURANCE: first_row.get(PT.INDUSTRIAL_INSURANCE, 0),
                        PT.LIFE_INSURANCE: first_row.get(PT.LIFE_INSURANCE, 0),
                        PT.CALIFORNIA_SDI: first_row.get(PT.CALIFORNIA_SDI, 0),
                        PT.FAMLI_TAX: first_row.get(PT.FAMLI_TAX, 0)
                    },
                    CA.NET_PAY: first_row.get(CA.NET_PAY),
                    EE.IS_BLIND: first_row.get(EE.IS_BLIND),
                    EE.STATEMENT_OF_EXEMPTION_RECEIVED_DATE: first_row.get(EE.STATEMENT_OF_EXEMPTION_RECEIVED_DATE),
                    # EE.DEBT_TYPE: first_row.get(EE.DEBT_TYPE),
                    EE.GARN_START_DATE: first_row.get(EE.GARN_START_DATE),
                    EE.NON_CONSUMER_DEBT: first_row.get(EE.NON_CONSUMER_DEBT),
                    EE.CONSUMER_DEBT: first_row.get(EE.CONSUMER_DEBT),
                    EE.AGE: first_row.get(EE.AGE),
                    EE.SPOUSE_AGE: first_row.get(EE.SPOUSE_AGE),
                    EE.IS_SPOUSE_BLIND: first_row.get(EE.IS_SPOUSE_BLIND),
                    EE.SUPPORT_SECOND_FAMILY: first_row.get(EE.SUPPORT_SECOND_FAMILY),
                    EE.NO_OF_DEPENDENT_CHILD: first_row.get(EE.NO_OF_DEPENDENT_CHILD, 0),
                    EE.ARREARS_GREATER_THAN_12_WEEKS: first_row.get(EE.ARREARS_GREATER_THAN_12_WEEKS),
                    EE.GARNISHMENT_DATA: [garnishment_data]
                })
            output_json = clean_data_for_json(output_json)
            return Response(output_json, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key in data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": f"Data value error: {str(e)}"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChildSupportCalculationRules(APIView):
    """
    API view to get the withholding limit rule data for a specific state.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Withholding limit rule data retrieved successfully'),
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def get(self, request, state, employee_id, supports_2nd_family, arrears_of_more_than_12_weeks, de, no_of_order):
        """
        Retrieve the withholding limit rule data for a specific state and employee.
        """
        try:
            # Normalize state name
            state_name = StateAbbreviations(state).get_state_name_and_abbr()
            file_path = os.path.join(
                settings.BASE_DIR,
                'User_app',
                'configuration files/child support tables/withholding_rules.json'
            )

            # Read the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)

            ccpa_rules_data = data.get("WithholdingRules", [])
            # Find the record for the given state
            records = next(
                (rec for rec in ccpa_rules_data if rec['state'].lower() == state_name.lower()), None)

            if not records:
                return Response({
                    'success': False,
                    'message': 'State not found',
                    'status_code': status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            # Determine DE > 145 logic
            try:
                de_gt_145 = "No" if float(de) <= 145 or records.get(
                    "rule") != "Rule_6" else "Yes"
            except Exception:
                de_gt_145 = "No"

            # Adjust arrears_of_more_than_12_weeks for Rule_4
            arrears_val = "" if records.get(
                "rule") == "Rule_4" else arrears_of_more_than_12_weeks

            # Determine order_gt_one logic for Rule_4
            try:
                order_gt_one = "No" if int(no_of_order) > 1 or records.get(
                    "rule") != "Rule_4" else "Yes"
            except Exception:
                order_gt_one = "No"

            # Identify withholding limit using state rules
            try:
                wl_limit = WLIdentifier().find_wl_value(
                    state_name, employee_id, supports_2nd_family, arrears_val, de_gt_145, order_gt_one
                )
                records["applied_withholding_limit"] = round(
                    wl_limit * 100, 0) if isinstance(wl_limit, (int, float)) else wl_limit
            except Exception as e:
                return Response({
                    "success": False,
                    "message": f"Error calculating withholding limit: {str(e)}",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Get mapping keys for mandatory deductions
            try:
                mapping_keys = ChildSupport(state_name).get_mapping_keys()
                result = {}
                for item in mapping_keys:
                    key = item.split("_")[0]
                    result[key] = item
                records["mandatory_deductions"] = result
            except Exception as e:
                records["mandatory_deductions"] = {}
                # Optionally log this error

            response_data = {
                'success': True,
                'message': 'Data retrieved successfully',
                'status_code': status.HTTP_200_OK,
                'data': records
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # logger.error(f"Error in ChildSupportCalculationRules: {e}")
            return Response({
                "success": False,
                "message": f"Error retrieving child support calculation rules: {str(e)}",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GarnishmentOrderImportView(APIView):
    """
    API view to handle the import of garnishment orders from a file.
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
                description="Excel file to upload"
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
            201: 'File processed successfully',
            400: 'No file provided or unsupported file format',
            500: 'Internal server error'
        }
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
                return Response(
                    {"error": "Unsupported file format. Please upload a CSV or Excel file."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            orders = []
            for _, row in df.iterrows():
                try:
                    order_data = {
                        "start_date": row.get("start_date"),
                        "end_date": row.get("end_date"),
                        "amount": row.get("amount"),
                        "arrear_greater_than_12_weeks": row.get("arrear_greater_than_12_weeks"),
                        "arrear_amount": row.get("arrear_amount"),
                        "record_updated": row.get("record_updated"),
                        "case_id": row.get("case_id"),
                        "work_state": row.get("work_state"),
                        "type": row.get("type"),
                        "sdu": row.get("sdu"),
                        "eeid": row.get("eeid"),
                        "fein": row.get("fein")
                    }
                    serializer = GarnishmentOrderSerializer(data=order_data)
                    if serializer.is_valid():
                        orders.append(serializer.save())
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                except Exception as row_e:
                    return Response(
                        {"error": f"Error processing row: {str(row_e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            LogEntry.objects.create(
                action='Garnishment Orders Imported',
                details='Garnishment orders imported Successfully using file.'
            )

            return Response(
                {"message": "File processed successfully",
                    "status_code": status.HTTP_201_CREATED},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # logger.error(f"Error importing garnishment orders: {e}")
            return ValueError(
                {'error': str(
                    e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Extracting the Last Five record from the Log Table


class LastFiveLogsView(APIView):
    """
    API view to fetch the last five log entries.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Success', LogSerializer(many=True)),
            500: 'Internal server error'
        }
    )
    def get(self, request, format=None):
        try:
            logs = LogEntry.objects.order_by('-timestamp')[:5]
            serializer = LogSerializer(logs, many=True)
            response_data = {
                'success': True,
                'message': 'Data fetched successfully',
                'status_code': status.HTTP_200_OK,
                'data': serializer.data
            }
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            # logger.error(f"Error fetching last five logs: {e}")
            return ValueError(
                {
                    "error": str(e),
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpsertGarnishmentOrderView(APIView):
    """
    API view to upsert (insert or update) garnishment orders from an uploaded Excel or CSV file.
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
                description="Excel file to upload"
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
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read file based on extension
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
                # Clean up row keys and values
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
                                parsed_date = pd.to_datetime(
                                    value, errors='coerce')
                                row[field] = parsed_date.strftime(
                                    '%Y-%m-%d') if not pd.isnull(parsed_date) else None
                        except Exception:
                            row[field] = None

                case_id = row.get(EE.CASE_ID)
                if not case_id:
                    # Skip row if unique identifiers are missing
                    continue

                obj = garnishment_order.objects.filter(case_id=case_id).first()

                if obj:
                    # Only update if there are changes
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
                    'message': 'Garnishment order(s) added successfully',
                    'added_orders': added_orders
                })
            if updated_orders:
                response_data.append({
                    'message': 'Garnishment order(s) updated successfully',
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
            # logger.error(f"Error upserting garnishment orders: {e}")
            return Response({
                'success': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExportGarnishmentOrderDataView(APIView):
    """
    API view to export garnishment order data as an Excel file.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: 'Excel file exported successfully',
            404: 'No garnishment orders found',
            500: 'Internal server error'
        }
    )
    def get(self, request):
        """
        Handles GET request to export all garnishment orders to an Excel file.
        """
        try:
            # Fetch all garnishment orders from the database
            orders = garnishment_order.objects.all()
            if not orders.exists():
                return JsonResponse(
                    {
                        'detail': 'No garnishment orders found',
                        'status': status.HTTP_404_NOT_FOUND
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = GarnishmentOrderSerializer(orders, many=True)

            # Create Excel workbook and worksheet
            wb = Workbook()
            ws = wb.active
            ws.title = "Garnishment Orders"

            # Define header fields (use constants where available)
            header_fields = [
                "eeid", "fein", EE.CASE_ID, EE.WORK_STATE, EE.GARNISHMENT_TYPE, "sdu",
                "start_date", "end_date", "amount", EE.ARREARS_GREATER_THAN_12_WEEKS,
                CA.ARREAR_AMOUNT, "record_updated"
            ]
            ws.append(header_fields)

            # Write data rows to the worksheet
            for order in serializer.data:
                row = [order.get(field, '') for field in header_fields]
                ws.append(row)

            # Save workbook to in-memory buffer
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            # Prepare HTTP response with Excel content
            filename = f'garnishment_orders_{datetime.today().strftime("%m-%d-%y")}.xlsx'
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            # logger.error(f"Error exporting garnishment order data: {e}")
            return JsonResponse(
                {
                    'detail': f'Error exporting garnishment order data: {str(e)}',
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GarnishmentFeesRules(APIView):
    """
    API view for CRUD operations on garnishment fees rules.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Success', GarnishmentFeesRulesSerializer(many=True)),
            404: 'Rule not found',
            500: 'Internal server error'
        }
    )
    def get(self, request, Rule=None):
        """
        Retrieve a specific garnishment fee rule by Rule or all rules if Rule is not provided.
        """
        try:
            if Rule:
                rule_obj = garnishment_fees_rules.objects.get(rule=Rule)
                serializer = GarnishmentFeesRulesSerializer(rule_obj)
                return ResponseHelper.success_response('Rule data fetched successfully', serializer.data)
            else:
                rules = garnishment_fees_rules.objects.all()
                serializer = GarnishmentFeesRulesSerializer(
                    rules, many=True)
                return ResponseHelper.success_response('All rules fetched successfully', serializer.data)
        except garnishment_fees_rules.DoesNotExist:
            return ResponseHelper.error_response(f'Rule "{Rule}" not found', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=GarnishmentFeesRulesSerializer,
        responses={
            201: openapi.Response('Created', GarnishmentFeesRulesSerializer),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new garnishment fee rule.
        """
        try:
            serializer = GarnishmentFeesRulesSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Rule created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=GarnishmentFeesRulesSerializer,
        responses={
            200: openapi.Response('Updated', GarnishmentFeesRulesSerializer),
            400: 'Invalid data',
            404: 'Rule not found',
            500: 'Internal server error'
        }
    )
    def put(self, request, rule=None):
        """
        Update an existing garnishment fee rule by Rule.
        """
        if not rule:
            return ResponseHelper.error_response('Rule is required in URL to update data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            rule_obj = garnishment_fees_rules.objects.get(rule=rule)
        except garnishment_fees_rules.DoesNotExist:
            return ResponseHelper.error_response(f'Rule "{rule}" not found', status_code=status.HTTP_404_NOT_FOUND)
        try:
            serializer = GarnishmentFeesRulesSerializer(
                rule_obj, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Rule updated successfully', serializer.data)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while updating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={
            200: 'Rule deleted successfully',
            400: 'Rule is required in URL to delete data',
            404: 'Rule not found',
            500: 'Internal server error'
        }
    )
    def delete(self, request, rule=None):
        """
        Delete a garnishment fee rule by Rule.
        """
        if not rule:
            return ResponseHelper.error_response('Rule is required in URL to delete data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            rule_obj = garnishment_fees_rules.objects.get(rule=rule)
            rule_obj.delete()
            return ResponseHelper.success_response(f'Rule "{rule}" deleted successfully')
        except garnishment_fees_rules.DoesNotExist:
            return ResponseHelper.error_response(f'Rule "{rule}" not found', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while deleting data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_single_file(file):
    """
    Handles the upload, storage, and analysis of a single PDF file.
    Returns serialized data or error details.
    """
    try:
        file_bytes = file.read()
        endpoint = os.getenv("AZURE_ENDPOINT")
        key = os.getenv("AZURE_KEY")

        if not endpoint or not key:
            raise ValueError("Azure endpoint or key not configured.")

        # Upload file to blob storage
        blob_info = put(f"PDFFiles/{file.name}", file_bytes)
        blob_url = blob_info.get("url")
        if not blob_url:
            raise ValueError("Failed to upload file to blob storage.")

        # Save file record in database
        obj = IWOPDFFiles.objects.create(name=file.name, pdf_url=blob_url)
        serializer = IWOPDFFilesSerializer(obj)

        # Analyze file content using Azure Form Recognizer
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
            documents_data.append({"fields": fields})

        # Save extracted data to withholding_order_data model
        if documents_data:
            withholding_order_data.objects.create(
                **documents_data[0]["fields"])

        return serializer.data

    except Exception as e:
        # Log the error if logging is set up
        # logger.error(f"Error in handle_single_file: {e}")
        return {
            'success': False,
            'message': 'Error occurred while uploading the file',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'data': None,
            "error": str(e)
        }


file_upload_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'file': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_BINARY),
            description="Upload one or more PDF files"
        ),
    },
    required=['file']
)


class PDFUploadView(APIView):
    """
    API view to handle uploading and processing of multiple PDF files.
    """

    @swagger_auto_schema(
        operation_description="Upload one or more PDF files",
        request_body=file_upload_schema,
        responses={
            201: openapi.Response(description="PDF files uploaded successfully"),
            400: openapi.Response(description="No files provided"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    def post(self, request):
        try:
            files = request.FILES.getlist("file")
            if not files:
                return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)

            results = []
            for file in files:
                result = handle_single_file(file)
                results.append(result)

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
    """
    API view to retrieve withholding order data for given IDs.
    Provides robust exception handling and clear response messages.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Get 'ids' parameter from query string
            ids_param = request.query_params.get('ids')
            if not ids_param:
                return Response({
                    'success': False,
                    'message': 'No IDs provided in query parameters.',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            # Split and clean IDs
            ids = [id_.strip()
                   for id_ in ids_param.split(',') if id_.strip().isdigit()]
            if not ids:
                return Response({
                    'success': False,
                    'message': 'No valid IDs provided.',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            # Query the database for matching records
            files = withholding_order_data.objects.filter(id__in=ids)
            if not files.exists():
                return Response({
                    'success': False,
                    'message': 'No data found for the provided IDs.',
                    'status_code': status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = WithholdingOrderDataSerializers(files, many=True)
            response_data = {
                'success': True,
                'message': 'Data retrieved successfully',
                'status_code': status.HTTP_200_OK,
                'data': serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # logger.error(f"Error retrieving IWO PDF data: {e}")
            response_data = {
                'success': False,
                'message': 'Failed to retrieve data',
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error': str(e)
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GarnishmentOrderDetails(APIView):
    """
    API view for CRUD operations on garnishment order details.
    Provides robust exception handling and clear response messages.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Success', GarnishmentOrderSerializer(many=True)),
            404: 'Not found',
            500: 'Internal server error'
        }
    )
    def get(self, request, case_id=None):
        """
        Retrieve garnishment order details by case_id or all orders if case_id is not provided.
        """
        try:
            if case_id:
                try:
                    order = garnishment_order.objects.get(case_id=case_id)
                    serializer = GarnishmentOrderSerializer(order)
                    return ResponseHelper.success_response(
                        f'Garnishment order details for case_id "{case_id}" fetched successfully',
                        serializer.data
                    )
                except garnishment_order.DoesNotExist:
                    return ResponseHelper.error_response(
                        f'case_id "{case_id}" not found',
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            else:
                orders = garnishment_order.objects.all()
                serializer = GarnishmentOrderSerializer(orders, many=True)
                return ResponseHelper.success_response(
                    'All data fetched successfully',
                    serializer.data
                )
        except Exception as e:
            return ResponseHelper.error_response(
                'Failed to fetch data',
                str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=GarnishmentOrderSerializer,
        responses={
            201: openapi.Response('Created', GarnishmentOrderSerializer),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new garnishment order.
        """
        try:
            serializer = GarnishmentOrderSerializer(data=request.data)
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
        request_body=GarnishmentOrderSerializer,
        responses={
            200: openapi.Response('Updated', GarnishmentOrderSerializer),
            400: 'Invalid data',
            404: 'Not found',
            500: 'Internal server error'
        }
    )
    def put(self, request, case_id=None):
        """
        Update an existing garnishment order by case_id.
        """
        if not case_id:
            return ResponseHelper.error_response(
                'case_id is required in URL to update data',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = garnishment_order.objects.get(case_id=case_id)
        except garnishment_order.DoesNotExist:
            return ResponseHelper.error_response(
                f'case_id "{case_id}" not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        try:
            serializer = GarnishmentOrderSerializer(order, data=request.data)
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
            200: 'Deleted successfully',
            400: 'case_id is required in URL to delete data',
            404: 'Not found',
            500: 'Internal server error'
        }
    )
    def delete(self, request, case_id=None):
        """
        Delete a garnishment order by case_id.
        """
        if not case_id:
            return ResponseHelper.error_response(
                'case_id is required in URL to delete data',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = garnishment_order.objects.get(case_id=case_id)
            order.delete()
            return ResponseHelper.success_response(
                f'Data for case_id "{case_id}" deleted successfully'
            )
        except garnishment_order.DoesNotExist:
            return ResponseHelper.error_response(
                f'case_id "{case_id}" not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return ResponseHelper.error_response(
                'Internal server error while deleting data',
                str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
