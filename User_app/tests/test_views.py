import os
import django
import unittest
import json
from rest_framework import status
from rest_framework.test import APIClient
from django.conf import settings
from django.test import TestCase





from GarnishEdge_Project.garnishment_library.child_support import *

# Ensure Django settings are loaded before importing Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GarnishEdge_Project.settings") 
django.setup()


class GarnishmentCalculationTests(unittest.TestCase):
    def setUp(self):
        """Initialize API client before each test"""
        self.client = APIClient()
        self.url = "http://127.0.0.1:8000/User/garnishment_calculate/"

    def test_calculation_data_view_success(self):
        # Load request data
        request_path = os.path.join(settings.BASE_DIR, 'User_app', 'tests', 'request.json')
        with open(request_path, 'r') as file:
            request_data = json.load(file)

        # Load expected response data
        response_path = os.path.join(settings.BASE_DIR, 'User_app', 'tests', 'response.json')
        with open(response_path, 'r') as file:
            expected_response_data = json.load(file)

        # Make POST request
        response = self.client.post(self.url, data=request_data, format="json")

        # Assert status code
        self.assertEqual(response.status_code, 200, msg="Expected status code 200")

        # Assert top-level response
        response_data = response.json()
        self.assertEqual(response_data["status_code"], expected_response_data["status_code"])
        self.assertEqual(response_data["message"], expected_response_data["message"])
        self.assertEqual(response_data["batch_id"], expected_response_data["batch_id"])
        self.assertEqual(len(response_data["results"]), len(expected_response_data["results"]))
        self.assertEqual(len(response_data["results"]), len(expected_response_data["results"]))

        # Sort both results by ee_id to ensure correct comparison
        sorted_actual_results = sorted(response_data["results"], key=lambda x: x["ee_id"])
        sorted_expected_results = sorted(expected_response_data["results"], key=lambda x: x["ee_id"])


        # Compare results individually
        for actual, expected in zip(sorted_actual_results, sorted_expected_results):

            self.assertEqual(actual["ee_id"], expected["ee_id"])

            for garnishment in actual.get("garnishment_data", []):
                garnishment_type = garnishment["type"].lower()

                if garnishment_type == "child support":
                    agency_child_support = next(
                        (block for block in actual["agency"] if "withholding_amt" in block), None)
                    agency_arrear = next(
                        (block for block in actual["agency"] if "Arrear" in block), None)

                    expected_agency_child_support = next(
                        (block for block in expected["agency"] if "withholding_amt" in block), None)
                    expected_agency_arrear = next(
                        (block for block in expected["agency"] if "Arrear" in block), None)
                    
                    # print(f"Agency Child Support: {agency_child_support}")
                    # print(f"Expected Agency Child Support: {expected_agency_child_support}")

                    # actual_support_amt = agency_child_support["withholding_amt"][0]["child_support"]
                    # expected_support_amt = expected_agency_child_support["withholding_amt"][0]["child_support"]

                    # actual_arrear = agency_arrear["Arrear"][0]["arrear_amount"]
                    # expected_arrear = expected_agency_arrear["Arrear"][0]["arrear_amount"]
                    self.assertEqual(agency_child_support, expected_agency_child_support,
                                     f"Child support mismatch for {actual['ee_id']}")

                    self.assertEqual(agency_arrear, expected_agency_arrear,
                                     f"Arrear amount mismatch for {actual['ee_id']}")

                elif garnishment_type == "state tax levy":
                    agency_block = next(
                        (block for block in actual["agency"] if "withholding_amt" in block), None)
                    expected_agency_block = next(
                        (block for block in expected["agency"] if "withholding_amt" in block), None)

                    actual_garnishment_amt = agency_block["withholding_amt"][0]["garnishment_amount"]
                    expected_garnishment_amt = expected_agency_block["withholding_amt"][0]["garnishment_amount"]

                    self.assertAlmostEqual(actual_garnishment_amt, expected_garnishment_amt, places=2,
                                           msg=f"State tax levy mismatch for {actual['ee_id']}")

class CalculationDataStuctureTests(unittest.TestCase):
    def setUp(self):
        """Initialize API client before each test"""
        self.client = APIClient()
        self.url = "http://127.0.0.1:8000/User/garnishment_calculate/"

        
    def test_calculation_data_view_invalid_garnishment_type(self):
        test_data = {
            "batch_id": "B001A",
            "cid": {
                "C00001": {
                    "employees": [
                        {
                            "ee_id": "EE005114",
                            "garnishment_data": [{"type": "Student Default Loanss", "data": []}]
                        }
                    ]
                }
            }
        }


        response = self.client.post(self.url, data=test_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_calculation_data_view_missing_batch_id(self):
        test_data = {"cid": {}}
        response = self.client.post(self.url, data=test_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "batch_id is required")

# class ExcelToJSONAPITest(unittest.TestCase):
#     def setUp(self):
#         """Initialize API client before each test"""
#         self.client = APIClient()
#         self.url = "http://127.0.0.1:8000/User/ConvertExcelToJson/"

#     def test_calculation_data_view_success(self):
#         # Load request data
#         request_path = os.path.join(settings.BASE_DIR, 'User_app', 'tests', 'request.json')
#         with open(request_path, 'r') as file:
#             request_data = json.load(file)


if __name__ == "__main__":
    unittest.main()





# class ChildSupportTests(unittest.TestCase):

#     def test_child_support_result(self):
#         """Test child support calculation"""
#         test_data=os.path.join(settings.BASE_DIR, 'User_app', 'tests/test_data.json')
#         with open(test_data, 'r') as file:
#             data = json.load(file)
            
#         tcsa = ChildSupport().get_list_supportAmt(data)
#         result=list(MultipleChild().calculate(data) if len(tcsa) > 1 else SingleChild().calculate(data))

#         for i in range(len(data["result"])):
#             for k,v in data["result"][i].items():
#                 self.assertEqual(data["result"][i][k], result[i][k])
