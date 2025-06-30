from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import IWO_Details_PDF, garnishment_fees, APICallLog
from ..serializers import GarnishmentFeesSerializer
from django.db.models import Count
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse


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
