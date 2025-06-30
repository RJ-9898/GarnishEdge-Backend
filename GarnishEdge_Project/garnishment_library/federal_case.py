import json
import os
import re
from GarnishEdge_Project import settings
from User_app.constants import FilingStatusFields, EmployeeFields, CalculationFields, JSONPath
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import traceback as t


class FederalTaxCalculation:
    """
    Handles federal tax exemption calculations based on employee and spouse details.
    """

    def get_json_file_path(self, filing_status, statement_of_exemption_received_date, file_type="standard"):
        """
        Returns the file path for the given filing status and file type.
        :param filing_status: str - Filing status like 'single', 'head_of_household', etc.
        :param file_type: str - Type of exemption file: 'standard', 'additional'
        :return: str - Full path to the JSON file
        """

        # Extract year from date string (assumes last 4 chars are year)
        formated_date = statement_of_exemption_received_date[-4:]

        # Clean and normalize filing status
        filing_status = os.path.basename(str(filing_status)).lower()

        # Safely join all folders to avoid mixed slashes
        base_path = os.path.join(
            settings.BASE_DIR, 'User_app', 'configuration files', 'federal tables', formated_date
        )

        if file_type == "additional":
            path = os.path.join(base_path, 'additional_exempt_amount.json')
            return path

        # For standard exemption amounts
        if filing_status in [
            FilingStatusFields.QUALIFYING_WIDOWERS,
            FilingStatusFields.MARRIED_FILING_JOINT_RETURN
        ]:
            path = os.path.join(base_path, 'married_filing_joint_return.json')
            return path

        # Default standard path
        path = os.path.join(base_path, f'{filing_status}.json')
        return path

    def get_file_data(self, file_path):
        """
        Loads and returns JSON data from the given file path.
        Raises descriptive exceptions on failure.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {e}")

    def get_total_exemption_self(self, request):
        """
        Calculates the number of exemptions for the employee based on age and blindness.
        """
        age = request.get(EmployeeFields.AGE, 0)
        is_blind = request.get(EmployeeFields.IS_BLIND, False)
        if age >= 65 and is_blind:
            return 2
        elif is_blind or age >= 65:
            return 1
        return 0

    def get_total_exemption_dependent(self, request):
        """
        Calculates the number of exemptions for the spouse based on age and blindness.
        """
        spouse_age = request.get(EmployeeFields.SPOUSE_AGE, 0)
        is_spouse_blind = request.get(EmployeeFields.IS_SPOUSE_BLIND, False)
        if spouse_age >= 65 and is_spouse_blind:
            return 2
        elif is_spouse_blind or spouse_age >= 65:
            return 1
        return 0

    def get_additional_exempt_for_self(self, record):
        """
        Retrieves the additional exemption amount for the employee.
        """
        pay_period = record.get(EmployeeFields.PAY_PERIOD, "").lower()
        filing_status = record.get(EmployeeFields.FILING_STATUS)
        no_of_exemption = self.get_total_exemption_self(record)
        statement_of_exemption_received_date = record.get(
            EmployeeFields.STATEMENT_OF_EXEMPTION_RECEIVED_DATE)

        file_path = self.get_json_file_path(
            filing_status, statement_of_exemption_received_date, file_type="additional")
        try:
            data = self.get_file_data(file_path)
            data = data[FilingStatusFields.ADDITIONAL_EXEMPT_AMOUNT]
        except Exception as e:
            raise ValueError(f"Failed to load or parse JSON data: {e}")

        if not data:
            raise ValueError(
                "No data found in the JSON for additional exempt amount.")

        # Filter by both number of exemptions and filing status
        filtered = []

        for item in data:
            if item.get(EmployeeFields.NO_OF_EXEMPTION_INCLUDING_SELF) == no_of_exemption:
                filtered.append(item)
        if not filtered:
            raise ValueError(
                f"No data found for {no_of_exemption} exemptions and filing status '{filing_status}'.")

        # Now get the value for the pay period
        value = filtered[0].get(pay_period)
        if value is None:
            raise ValueError(
                f"Pay period '{pay_period}' not found in entry: {filtered[0]}"
            )
        return value

    def get_additional_exempt_for_dependent(self, record):
        """
        Retrieves the additional exemption amount for the spouse/dependent.
        """
        pay_period = record.get(EmployeeFields.PAY_PERIOD).lower()
        filing_status = record.get(EmployeeFields.FILING_STATUS)
        no_of_exemption = self.get_total_exemption_dependent(record)
        statement_of_exemption_received_date = record.get(
            EmployeeFields.STATEMENT_OF_EXEMPTION_RECEIVED_DATE)

        file_path = self.get_json_file_path(
            filing_status, statement_of_exemption_received_date, file_type="additional")

        try:
            data = self.get_file_data(file_path)
            data = data[EmployeeFields.FILING_STATUS]
        except Exception as e:
            raise ValueError(f"Failed to load or parse JSON data: {e}")

        if not data:
            raise ValueError(
                "No data found in the JSON for additional exempt amount.")

        filtered = [
            item for item in data
            if item.get(EmployeeFields.NO_OF_EXEMPTION_INCLUDING_SELF) == no_of_exemption
        ]
        if not filtered:
            raise ValueError(
                f"No data found for {no_of_exemption} exemptions.")

        grouped = {
            FilingStatusFields.SINGLE: [],
            FilingStatusFields.HEAD_OF_HOUSEHOLD: [],
            "other": []
        }
        for item in filtered:
            status = item.get(EmployeeFields.FILING_STATUS)
            if status == FilingStatusFields.SINGLE:
                grouped[FilingStatusFields.SINGLE].append(item)
            elif status == FilingStatusFields.HEAD_OF_HOUSEHOLD:
                grouped[FilingStatusFields.HEAD_OF_HOUSEHOLD].append(item)
            else:
                grouped["other"].append(item)

        def safe_get_value(group_list, key):
            if not group_list:
                raise ValueError(
                    f"No entries found for filing status '{filing_status}' with {no_of_exemption} exemptions."
                )
            value = group_list[0].get(key)
            if value is None:
                raise ValueError(
                    f"Pay period '{key}' not found in entry: {group_list[0]}"
                )
            return value

        if filing_status == FilingStatusFields.SINGLE:
            return safe_get_value(grouped[FilingStatusFields.SINGLE], pay_period)
        elif filing_status == FilingStatusFields.HEAD_OF_HOUSEHOLD:
            return safe_get_value(grouped[FilingStatusFields.HEAD_OF_HOUSEHOLD], pay_period)
        else:
            return safe_get_value(grouped["other"], pay_period)

    def get_standard_exempt_amt(self, record):
        """
        Retrieves the standard exemption amount based on filing status and exemptions.
        """
        filing_status = record.get(EmployeeFields.FILING_STATUS)
        no_of_exemption_for_self = record.get(
            EmployeeFields.NO_OF_EXEMPTION_INCLUDING_SELF)
        pay_period = record.get(EmployeeFields.PAY_PERIOD).lower()
        statement_of_exemption_received_date = record.get(
            EmployeeFields.STATEMENT_OF_EXEMPTION_RECEIVED_DATE)

        # Cap the number of exemptions at 6 for calculation
        exempt = 6 if no_of_exemption_for_self > 5 else no_of_exemption_for_self

        try:
            file_path = self.get_json_file_path(
                filing_status, statement_of_exemption_received_date, file_type="standard")
            data = self.get_file_data(file_path)
            key = FilingStatusFields.MARRIED_FILING_JOINT_RETURN if filing_status in [
                FilingStatusFields.QUALIFYING_WIDOWERS,
                FilingStatusFields.MARRIED_FILING_JOINT_RETURN
            ] else filing_status

            status_data = data.get(key, [])
        except Exception as e:
            raise ValueError(f"Failed to load or parse exemption table: {e}")

        # Find the matching pay period entry
        semimonthly_data = next(
            (item for item in status_data if item.get(
                "Pay Period", "").lower() == pay_period), None
        )
        if not semimonthly_data:
            raise ValueError(
                f"No data found for pay period '{pay_period}' in filing status '{filing_status}'.")

        if no_of_exemption_for_self <= 5:
            exempt_amount = semimonthly_data.get(str(exempt))
            if exempt_amount is None:
                raise ValueError(
                    f"Exemption amount not found for {exempt} exemptions.")
            return float(exempt_amount)
        else:
            exemp_amt = semimonthly_data.get(str(exempt))
            if not exemp_amt:
                raise ValueError(
                    f"Exemption amount not found for {exempt} exemptions.")

            numbers = re.findall(r'\d+\.?\d*', exemp_amt)
            if len(numbers) < 2:
                raise ValueError(f"Invalid exemption format: {exemp_amt}")
            exempt1 = float(numbers[0])
            exempt2 = float(numbers[1])
            return round((exempt1 + (exempt2 * no_of_exemption_for_self)), 2)


class FederalTax(FederalTaxCalculation):
    """
    Main class to calculate the federal tax deduction amount.
    """

    def calculate(self, record):
        """
        Calculates the deduction amount based on net pay and exemption rules.
        Returns a Response object on error.
        """
        try:
            net_pay = record.get(CalculationFields.NET_PAY, 0)
            age = record.get(EmployeeFields.AGE, 0)
            is_blind = record.get(EmployeeFields.IS_BLIND, False)
            spouse_age = record.get(EmployeeFields.SPOUSE_AGE, 0)
            is_spouse_blind = record.get(EmployeeFields.IS_SPOUSE_BLIND, False)

            # Calculate standard and additional exemptions
            standard_exempt_amt = self.get_standard_exempt_amt(record)
            exempt_amount_self = 0
            exempt_amount_dependent = 0

            if age >= 65 or is_blind:
                exempt_amount_self = self.get_additional_exempt_for_self(
                    record)
            if spouse_age >= 65 or is_spouse_blind:
                exempt_amount_dependent = self.get_additional_exempt_for_dependent(
                    record)

            total_exempt_amt = standard_exempt_amt + \
                exempt_amount_self + exempt_amount_dependent

            amount_deduct = round(net_pay - total_exempt_amt, 2)
            amount_deduct = max(amount_deduct, 0)
            return round(amount_deduct, 2)

        except Exception as e:
            return Response(
                {
                    "error": str(e),
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
