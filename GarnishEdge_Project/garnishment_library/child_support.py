import os
import json
from django.conf import settings
from GarnishEdge_Project.garnishment_library import gar_resused_classes as gc
from User_app.constants import (
    EmployeeFields, CalculationFields, PayrollTaxesFields,
    ChildSupportFields, JSONPath, AllocationMethods
)


class ChildSupport:
    """
    Handles child support garnishment calculations, including disposable earnings,
    withholding limits, and allocation methods.
    """

    def __init__(self, work_state):
        self.de_rules_file = os.path.join(
            settings.BASE_DIR, 'User_app', JSONPath.DISPOSABLE_EARNING_RULES
        )
        self.work_state = gc.StateAbbreviations(
            work_state
        ).get_state_name_and_abbr()

    def _load_json_file(self, file_path):
        """
        Loads and parses a JSON file.
        Raises descriptive exceptions on failure.
        """
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON format in file: {file_path} ({str(e)})")

    def calculate_deduction_rules(self):
        """
        Retrieves deduction rules for the current work state.
        """
        if not self.work_state:
            raise ValueError("State information is missing in the record.")
        data = self._load_json_file(self.de_rules_file)
        for rule in data.get("de", []):
            if rule['State'].lower() == self.work_state.lower():
                return rule['taxes_deduction']
        raise ValueError(f"No DE rule found for state: {self.work_state}")

    def get_mapping_keys(self):
        """
        Maps deduction rule keys to actual payroll tax keys.
        """
        keys = self.calculate_deduction_rules()
        actual_keys = self._load_json_file(
            self.de_rules_file).get("mapping", [])
        # Map each key to its corresponding value in the mapping, or keep the key if not found
        return [next((d[key] for d in actual_keys if key in d), key) for key in keys]

    def calculate_md(self, record):
        """
        Calculates mandatory deductions based on payroll taxes and deduction rules.
        """
        gross_pay = record.get(CalculationFields.GROSS_PAY)
        work_state = record.get(EmployeeFields.WORK_STATE)
        payroll_taxes = record.get(PayrollTaxesFields.PAYROLL_TAXES)

        if gross_pay is None or work_state is None or payroll_taxes is None:
            raise ValueError(
                f"Missing fields: {CalculationFields.GROSS_PAY}, {EmployeeFields.WORK_STATE}, or {PayrollTaxesFields.PAYROLL_TAXES}."
            )

        de_keys = self.get_mapping_keys()
        try:
            return sum(payroll_taxes.get(key, 0) for key in de_keys)
        except Exception as e:
            raise ValueError(
                f"Error calculating mandatory deductions: {str(e)}")

    def calculate_gross_pay(self, record):
        """
        Calculates gross pay as the sum of wages, commissions/bonuses, and non-accountable allowances.
        """
        try:
            return sum(
                record.get(field, 0)
                for field in [
                    CalculationFields.WAGES,
                    CalculationFields.COMMISSION_AND_BONUS,
                    CalculationFields.NON_ACCOUNTABLE_ALLOWANCES
                ]
            )
        except Exception as e:
            raise ValueError(f"Error calculating gross pay: {str(e)}")

    def calculate_de(self, record):
        """
        Calculates disposable earnings (gross pay minus mandatory deductions).
        """
        try:
            return self.calculate_gross_pay(record) - self.calculate_md(record)
        except Exception as e:
            raise ValueError(
                f"Error calculating disposable earnings: {str(e)}")

    def get_list_support_amt(self, record):
        """
        Retrieves a list of ordered child support amounts from the record.
        """
        try:
            return [
                val for item in record["garnishment_data"][0]["data"]
                for key, val in item.items()
                if key.lower().startswith(CalculationFields.ORDERED_AMOUNT)
            ]
        except Exception as e:
            raise ValueError(f"Error extracting support amounts: {str(e)}")

    def get_list_support_arrear_amt(self, record):
        """
        Retrieves a list of arrear amounts from the record.
        """
        try:
            return [
                val for item in record["garnishment_data"][0]["data"]
                for key, val in item.items()
                if key.lower().startswith(CalculationFields.ARREAR_AMOUNT)
            ]
        except Exception as e:
            raise ValueError(f"Error extracting arrear amounts: {str(e)}")

    def calculate_wl(self, record):
        """
        Calculates the withholding limit (WL) for the employee based on state rules.
        """
        try:
            employee_id = record.get(EmployeeFields.EMPLOYEE_ID)
            supports_2nd_family = record.get(
                EmployeeFields.SUPPORT_SECOND_FAMILY)
            arrears_12w = record.get(
                EmployeeFields.ARREARS_GREATER_THAN_12_WEEKS)
            state_rules = gc.WLIdentifier().get_state_rules(self.work_state)
            order_count = len(self.get_list_support_amt(record))
            de = self.calculate_de(record)

            de_gt_145 = "Yes" if state_rules == "Rule_6" and de > 145 else "No"
            arrears_12w = "" if state_rules == "Rule_4" else arrears_12w
            order_gt_one = "Yes" if state_rules == "Rule_4" and order_count <= 1 else "No"

            return gc.WLIdentifier().find_wl_value(
                self.work_state, employee_id, supports_2nd_family,
                arrears_12w, de_gt_145, order_gt_one
            )
        except Exception as e:
            raise ValueError(f"Error calculating withholding limit: {str(e)}")

    def calculate_twa(self, record):
        """
        Calculates the total withholding amount (TWA) as the sum of support and arrear amounts.
        """
        try:
            return sum(self.get_list_support_amt(record)) + sum(self.get_list_support_arrear_amt(record))
        except Exception as e:
            raise ValueError(
                f"Error calculating total withholding amount: {str(e)}")

    def calculate_ade(self, record):
        """
        Calculates the allowable disposable earnings (ADE).
        """
        try:
            return self.calculate_wl(record) * self.calculate_de(record)
        except Exception as e:
            raise ValueError(
                f"Error calculating allowable disposable earnings: {str(e)}")

    def calculate_wa(self, record):
        """
        Calculates the withholding amount (WA) as the minimum of ADE and total support amount.
        """
        try:
            return min(self.calculate_ade(record), sum(self.get_list_support_amt(record)))
        except Exception as e:
            raise ValueError(f"Error calculating withholding amount: {str(e)}")

    def calculate_each_child_support_amt(self, record):
        """
        Returns a dictionary of each child support amount keyed by order.
        """
        try:
            return {
                f"child support amount{i+1}": amt
                for i, amt in enumerate(self.get_list_support_amt(record))
            }
        except Exception as e:
            raise ValueError(
                f"Error calculating each child support amount: {str(e)}")

    def calculate_each_arrears_amt(self, record):
        """
        Returns a dictionary of each arrear amount keyed by order.
        """
        try:
            return {
                f"arrear amount{i+1}": amt
                for i, amt in enumerate(self.get_list_support_arrear_amt(record))
            }
        except Exception as e:
            raise ValueError(
                f"Error calculating each arrears amount: {str(e)}")


class SingleChild(ChildSupport):
    """
    Handles calculation for a single child support order.
    """

    def calculate(self, record):
        try:
            child_amt = self.get_list_support_amt(record)[0]
            arrear_amt = self.get_list_support_arrear_amt(record)[0]
            de = self.calculate_de(record)
            ade = self.calculate_ade(record)
            gross_pay = self.calculate_gross_pay(record)
            withholding = min(ade, child_amt)
            remaining = max(0, ade - child_amt)
            arrear = min(arrear_amt, remaining) if ade > child_amt else 0

            return {
                "result_amt": {"child support amount1": round(withholding, 2) if gross_pay > 0 else 0},
                "arrear_amt": {"arrear amount1": round(arrear, 2) if gross_pay > 0 else 0},
                "ade": ade,
                "de": de,
                "mde": self.calculate_md(record)
            }
        except Exception as e:
            raise ValueError(f"Error in SingleChild calculation: {str(e)}")


class MultipleChild(ChildSupport):
    """
    Handles calculation for multiple child support orders, including allocation methods.
    """

    def calculate(self, record):
        try:
            tcsa = self.get_list_support_amt(record)
            taa = self.get_list_support_arrear_amt(record)
            ade = self.calculate_ade(record)
            twa = self.calculate_twa(record)
            wa = self.calculate_wa(record)
            gross_pay = self.calculate_gross_pay(record)
            de = self.calculate_de(record)
            alloc_method = gc.AllocationMethodIdentifiers(
                self.work_state
            ).get_allocation_method()

            if ade >= twa:
                cs_amounts = self.calculate_each_child_support_amt(record)
                ar_amounts = self.calculate_each_arrears_amt(record)
            else:
                cs_amounts, ar_amounts = {}, {}
                if alloc_method == AllocationMethods.PRORATE:
                    # Prorate support amounts
                    cs_amounts = {
                        f"child support amount{i+1}": round((amt / twa) * ade, 2) if gross_pay > 0 else 0
                        for i, amt in enumerate(tcsa)
                    }
                    arrear_pool = wa - sum(tcsa)
                    total_arrears = sum(taa)
                    # Prorate arrear amounts
                    ar_amounts = {
                        f"arrear amount{i+1}": (
                            round((amt / total_arrears) * arrear_pool, 2)
                            if total_arrears and arrear_pool > 0 and gross_pay > 0 else 0
                        ) for i, amt in enumerate(taa)
                    }
                elif alloc_method == AllocationMethods.DEVIDEEQUALLY:
                    # Divide equally among orders
                    split_amt = round(ade / len(tcsa), 2) if tcsa else 0
                    cs_amounts = {
                        f"child support amount{i+1}": split_amt if gross_pay > 0 else 0
                        for i in range(len(tcsa))
                    }
                    arrear_pool = ade - sum(tcsa)
                    ar_amounts = {
                        f"arrear amount{i+1}": round(amt / len(taa), 2) if arrear_pool > 0 and gross_pay > 0 else 0
                        for i, amt in enumerate(taa)
                    }
                else:
                    raise ValueError(
                        "Invalid allocation method for garnishment.")

            return {
                "result_amt": cs_amounts,
                "arrear_amt": ar_amounts,
                "ade": ade,
                "de": de,
                "mde": self.calculate_md(record)
            }
        except Exception as e:
            raise ValueError(f"Error in MultipleChild calculation: {str(e)}")
