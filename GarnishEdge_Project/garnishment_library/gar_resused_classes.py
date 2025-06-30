import json
import os
from django.conf import settings
from GarnishEdge_Project.garnishment_library import gar_resused_classes as gc
from User_app.constants import ChildSupportFields, EmployeeFields, CalculationFields


class DisposableIncomeCalculator:
    """
    Calculates disposable income and monthly garnishment amount.
    """

    def __init__(self, x=0.25):
        self.x = x

    def calculate(self, gross_income):
        """
        Returns the monthly garnishment amount based on gross income.
        """
        disposable_earnings = round(gross_income, 2)
        monthly_garnishment_amount = disposable_earnings * self.x
        return monthly_garnishment_amount


class AllocationMethodIdentifiers:
    """
    Identifies allocation method for a given work state.
    """

    def __init__(self, work_state):
        # Normalize state name
        self.work_state = gc.StateAbbreviations(
            work_state).get_state_name_and_abbr().lower()

    def get_allocation_method(self):
        """
        Returns the allocation method for the state, or an error message if not found.
        """
        file_path = os.path.join(
            settings.BASE_DIR, 'User_app', 'configuration files/child support tables/withholding_rules.json'
        )
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            child_support_data = data.get("WithholdingRules", [])
            for record in child_support_data:
                if record.get('state', '').lower() == self.work_state:
                    return record.get('allocation_method', '').lower()
            return f"No allocation method found for the state: {self.work_state.capitalize()}."
        except FileNotFoundError:
            return f"File not found: {file_path}"
        except json.JSONDecodeError:
            return f"Invalid JSON format in file: {file_path}"
        except Exception as e:
            return f"Error reading allocation method: {e}"


class CalculateAmountToWithhold:
    """
    Calculates the amount to withhold for child support based on allocation method.
    """

    def __init__(self, allowed_amount_for_garnishment, amount_to_withhold, allocation_method_for_garnishment, number_of_child_support_order):
        self.allowed_amount_for_garnishment = allowed_amount_for_garnishment
        self.amount_to_withhold = amount_to_withhold
        self.allocation_method_for_garnishment = allocation_method_for_garnishment
        self.number_of_child_support_order = number_of_child_support_order

    def calculate(self, amount_to_withhold_child):
        """
        Returns the calculated amount to withhold for a child.
        """
        try:
            if (self.allowed_amount_for_garnishment - self.amount_to_withhold) >= 0:
                return amount_to_withhold_child
            elif self.allocation_method_for_garnishment == ChildSupportFields.PRORATE:
                ratio = amount_to_withhold_child / \
                    self.amount_to_withhold if self.amount_to_withhold else 0
                return self.allowed_amount_for_garnishment * ratio
            elif amount_to_withhold_child > 0 and self.number_of_child_support_order:
                return self.allowed_amount_for_garnishment / self.number_of_child_support_order
            else:
                return 0
        except Exception as e:
            raise ValueError(f"Error calculating amount to withhold: {e}")


class CalculateArrearAmountForChild:
    """
    Calculates the arrear amount for child support.
    """

    def __init__(self, amount_left_for_arrears, allowed_child_support_arrear, allocation_method_for_arrears, number_of_arrear):
        self.amount_left_for_arrears = amount_left_for_arrears
        self.allowed_child_support_arrear = allowed_child_support_arrear
        self.allocation_method_for_arrears = allocation_method_for_arrears
        self.number_of_arrear = number_of_arrear

    def calculate(self, arrears_amt_child):
        """
        Returns the calculated arrear amount for a child.
        """
        try:
            if (self.amount_left_for_arrears - self.allowed_child_support_arrear) >= 0:
                return arrears_amt_child
            elif self.allocation_method_for_arrears == ChildSupportFields.PRORATE:
                ratio = arrears_amt_child / \
                    self.allowed_child_support_arrear if self.allowed_child_support_arrear else 0
                return self.amount_left_for_arrears * ratio
            elif self.amount_left_for_arrears > 0 and self.number_of_arrear:
                return self.amount_left_for_arrears / self.number_of_arrear
            else:
                return 0
        except Exception as e:
            raise ValueError(f"Error calculating arrear amount: {e}")


class WLIdentifier:
    """
    Identifies withholding limits for a given state and employee.
    """

    def get_state_rules(self, work_state):
        """
        Returns the withholding rule for the given state.
        """
        file_path = os.path.join(
            settings.BASE_DIR, 'User_app', 'configuration files/child support tables/withholding_rules.json'
        )
        try:
            work_state_name = gc.StateAbbreviations(
                work_state).get_state_name_and_abbr()
            with open(file_path, 'r') as file:
                data = json.load(file)
            ccpa_rules_data = data.get("WithholdingRules", [])
            for record in ccpa_rules_data:
                if record.get('state', '').lower() == work_state_name.lower():
                    return record.get('rule')
            return f"No allocation method found for the state: {work_state_name.capitalize()}."
        except FileNotFoundError:
            return f"File not found: {file_path}"
        except json.JSONDecodeError:
            return f"Invalid JSON format in file: {file_path}"
        except Exception as e:
            return f"Error reading state rules: {e}"

    def find_wl_value(self, work_state, employee_id, supports_2nd_family, arrears_of_more_than_12_weeks, de_gt_145, order_gt_one):
        """
        Finds the withholding limit value for the employee based on rules.
        """
        file_path = os.path.join(
            settings.BASE_DIR, 'User_app', 'configuration files/child support tables/withholding_limits.json'
        )
        try:
            state_rule = self.get_state_rules(work_state)
            with open(file_path, 'r') as file:
                data = json.load(file)
            ccpa_limits_data = data.get("Rules", [])
            for rule in ccpa_limits_data:
                if rule.get("Rule") == state_rule:
                    for detail in rule.get("Details", []):
                        if (
                            (detail.get("Supports_2nd_family") == "" and detail.get("Arrears_of_more_than_12_weeks") == "") or
                            (
                                detail.get("Supports_2nd_family") == supports_2nd_family and
                                detail.get("Arrears_of_more_than_12_weeks") == arrears_of_more_than_12_weeks and
                                detail.get("de_gt_145") == de_gt_145 and
                                detail.get("order_gt_one") == order_gt_one
                            )
                        ):
                            wl_str = detail.get("WL", "0").replace("%", "")
                            try:
                                result = int(wl_str) / 100
                                return result
                            except ValueError:
                                continue
            return f"No matching WL found for this employee: {employee_id}"
        except FileNotFoundError:
            return f"File not found: {file_path}"
        except json.JSONDecodeError:
            return f"Invalid JSON format in file: {file_path}"
        except Exception as e:
            return f"Error finding WL value: {e}"


class GarnishmentFeesIdentifier:
    """
    Identifies garnishment fees for a given record.
    """
    @staticmethod
    def calculate(record):
        """
        Returns the garnishment fee amount for the record, or None if not found.
        """
        try:
            work_state = record.get(EmployeeFields.WORK_STATE, "").lower()
            pay_period = record.get(EmployeeFields.PAY_PERIOD, "").lower()
            gar_type = record.get("garnishment_data", [{}])[0]
            garnishment_type = gar_type.get(
                EmployeeFields.GARNISHMENT_TYPE, "").replace('_', ' ').title()
            file_path = os.path.join(
                settings.BASE_DIR, 'User_app', 'configuration files/child support tables/garnishment_fees.json'
            )
            with open(file_path, 'r') as file:
                data = json.load(file)
            for rule in data.get("fees", []):
                if (
                    rule.get("State", "").lower() == work_state and
                    rule.get("Type") == garnishment_type and
                    rule.get("Pay Period") == pay_period
                ):
                    return rule.get("Amount")
            return None
        except Exception as e:
            return f"Error calculating garnishment fees: {e}"


def change_record_case(record):
    """
    Converts all keys in the record to snake_case and lower case.
    """
    try:
        new_record = {}
        for key, value in record.items():
            new_key = key.replace(' ', '_').lower()
            new_record[new_key] = value
        return new_record
    except Exception as e:
        raise ValueError(f"Error changing record case: {e}")


class StateAbbreviations:
    """
    Utility for converting state abbreviations to full state names.
    """

    def __init__(self, abbreviation):
        self.abbreviation = abbreviation.lower()

    def get_state_name_and_abbr(self):
        """
        Returns the full state name for a given abbreviation, or the input if not found.
        """
        state_abbreviations = {
            "al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas",
            "ca": "california", "co": "colorado", "ct": "connecticut", "de": "delaware",
            "fl": "florida", "ga": "georgia", "hi": "hawaii", "id": "idaho",
            "il": "illinois", "in": "indiana", "ia": "iowa", "ks": "kansas",
            "ky": "kentucky", "la": "louisiana", "me": "maine", "md": "maryland",
            "ma": "massachusetts", "mi": "michigan", "mn": "minnesota", "ms": "mississippi",
            "mo": "missouri", "mt": "montana", "ne": "nebraska", "nv": "nevada",
            "nh": "new hampshire", "nj": "new jersey", "nm": "new mexico", "ny": "new york",
            "nc": "north carolina", "nd": "north dakota", "oh": "ohio", "ok": "oklahoma",
            "or": "oregon", "pa": "pennsylvania", "ri": "rhode island", "sc": "south carolina",
            "sd": "south dakota", "tn": "tennessee", "tx": "texas", "ut": "utah",
            "vt": "vermont", "va": "virginia", "wa": "washington", "wv": "west virginia",
            "wi": "wisconsin", "wy": "wyoming"
        }
        if len(self.abbreviation) != 2:
            state_name = self.abbreviation
        else:
            state_name = state_abbreviations.get(
                self.abbreviation, self.abbreviation)
        return state_name
