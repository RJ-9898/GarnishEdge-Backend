from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, date
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from User_app.models import (
    state_tax_levy_applied_rule, state_tax_levy_exempt_amt_config, employee_detail, state_tax_levy_rule,
    employee_batch_data, creditor_debt_applied_rule, garnishment_batch_data, payroll_taxes_batch_data, creditor_debt_exempt_amt_config
)
from User_app.serializers import (
    EmployeeDetailsSerializer, StateTaxLevyConfigSerializers, StateTaxLevyExemptAmtConfigSerializers, CreditorDebtExemptAmtConfigSerializers
)
from User_app.log_files.api_log import log_api
from GarnishEdge_Project.garnishment_library.gar_resused_classes import StateAbbreviations
from GarnishEdge_Project.garnishment_library.child_support import SingleChild, MultipleChild, ChildSupport
from GarnishEdge_Project.garnishment_library.student_loan import StudentLoanCalculator
from GarnishEdge_Project.garnishment_library.garnishment_fees import GarFeesRulesEngine
from GarnishEdge_Project.garnishment_library.federal_case import FederalTax
from GarnishEdge_Project.garnishment_library.state_tax import StateTaxLevyCalculator
from GarnishEdge_Project.garnishment_library.creditor_debt import CreditorDebtCalculator
from GarnishEdge_Project.garnishment_library.utility_class import ResponseHelper
from User_app.constants import (
    EmployeeFields as EE,
    GarnishmentTypeFields as GT,
    GarnishmentTypeResponse as GR,
    CalculationFields as CA,
    PayrollTaxesFields as PT,
    CalculationResponseFields as CR,
    CalculationMessages as CM,
    CommonConstants,
    BatchDetail
)
from User_app.exception_handler import log_and_handle_exceptions

logger = logging.getLogger(__name__)

INSUFFICIENT_PAY = "Garnishment cannot be deducted due to insufficient pay"


class CalculationDataView:
    """
    Service class to handle all garnishment calculations and database operations.
    """

    def preload_config_data(self, garnishment_types):
        """
        Preloads configuration data for the requested garnishment types.
        """
        config_data = {}
        try:
            if GT.STATE_TAX_LEVY in garnishment_types:
                queryset = state_tax_levy_exempt_amt_config.objects.all()
                serializer = StateTaxLevyExemptAmtConfigSerializers(
                    queryset, many=True)
                config_data[GT.STATE_TAX_LEVY] = serializer.data

            if GT.CREDITOR_DEBT in garnishment_types:
                queryset = creditor_debt_exempt_amt_config.objects.all()
                serializer = CreditorDebtExemptAmtConfigSerializers(
                    queryset, many=True)
                config_data[GT.CREDITOR_DEBT] = serializer.data
        except Exception as e:
            logger.error(f"Error preloading config data: {e}")
        return config_data

    def validate_fields(self, record, required_fields):
        """
        Validates required fields and returns a list of missing fields.
        Uses set operations for efficiency if required_fields is large.
        """
        if len(required_fields) > 10:
            return list(set(required_fields) - set(record))
        return [field for field in required_fields if field not in record]

    def _get_employee_details(self, employee_id):
        """
        Fetches employee details by ID.
        Returns serialized data or None if not found.
        """
        try:
            obj = employee_detail.objects.get(ee_id=employee_id)
            serializer = EmployeeDetailsSerializer(obj)
            return serializer.data
        except employee_detail.DoesNotExist:
            return None
        except Exception as e:
            logger.error(
                f"Error fetching employee details for {employee_id}: {e}")
            return None

    def is_garnishment_fee_deducted(self, record):
        """
        Determines if garnishment fees can be deducted for the employee.
        Returns True, False, or None (if employee not found).
        """
        employee_data = self._get_employee_details(
            record[EE.EMPLOYEE_ID])
        if employee_data is None:
            return None
        suspended_till_str = employee_data.get(
            'garnishment_fees_suspended_till')
        if not suspended_till_str:
            return True
        try:
            suspended_date = datetime.strptime(
                suspended_till_str, "%Y-%m-%d").date()
            return date.today() >= suspended_date
        except Exception as e:
            logger.warning(
                f"Malformed suspension date for employee {record[EE.EMPLOYEE_ID]}: {e}")
            return True

    def get_garnishment_fees(self, record, total_withhold_amt):
        """
        Calculates garnishment fees based on employee data and suspension status.
        """
        is_deductible = self.is_garnishment_fee_deducted(record)
        employee_id = record.get(EE.EMPLOYEE_ID)
        work_state = record.get(EE.WORK_STATE)
        try:
            if is_deductible is None:
                fees = GarFeesRulesEngine(work_state).apply_rule(
                    record, total_withhold_amt)
                return f"{fees}, {employee_id} is not registered. Please register the employee first to suspend garnishment fees calculation."
            elif is_deductible:
                return GarFeesRulesEngine(work_state).apply_rule(record, total_withhold_amt)
            else:
                employee_data = self._get_employee_details(employee_id)
                suspended_date = employee_data.get(
                    'garnishment_fees_suspended_till', 'N/A')
                return f"Garnishment fees cannot be deducted due to the suspension of garnishment fees until {suspended_date}"
        except Exception as e:
            logger.error(
                f"Error calculating garnishment fees for {employee_id}: {e}")
            return f"Error calculating garnishment fees: {e}"

    def get_rounded_garnishment_fee(self, work_state, record, withholding_amt):
        """
        Applies garnishment fee rule and rounds the result if it is numeric.
        """
        try:
            fee = GarFeesRulesEngine(work_state).apply_rule(
                record, withholding_amt)
            if isinstance(fee, (int, float)):
                return round(fee, 2)
            return fee
        except Exception as e:
            logger.error(f"Error rounding garnishment fee: {e}")
            return f"Error calculating garnishment fee: {e}"

    def calculate_garnishment(self, garnishment_type, record, config_data):
        """
        Handles garnishment calculations based on type.
        """
        garnishment_type_lower = garnishment_type.lower()
        garnishment_rules = {
            GT.CHILD_SUPPORT: {
                "fields": [
                    EE.ARREARS_GREATER_THAN_12_WEEKS, EE.SUPPORT_SECOND_FAMILY,
                    CA.GROSS_PAY, PT.PAYROLL_TAXES
                ],
                "calculate": self.calculate_child_support

            },
            GT.FEDERAL_TAX_LEVY: {
                "fields": [EE.FILING_STATUS, EE.PAY_PERIOD, CA.NET_PAY, EE.AGE, EE.IS_BLIND, EE.STATEMENT_OF_EXEMPTION_RECEIVED_DATE],
                "calculate": self.calculate_federal_tax
            },
            GT.STUDENT_DEFAULT_LOAN: {
                "fields": [CA.GROSS_PAY, EE.PAY_PERIOD, EE.NO_OF_STUDENT_DEFAULT_LOAN, PT.PAYROLL_TAXES],
                "calculate": self.calculate_student_loan
            },
            GT.STATE_TAX_LEVY: {
                "fields": [
                    EE.GROSS_PAY, EE.WORK_STATE
                ],
                "calculate": self.calculate_state_tax_levy
            },
            GT.CREDITOR_DEBT: {
                "fields": [
                    EE.GROSS_PAY, EE.WORK_STATE, EE.PAY_PERIOD, EE.FILING_STATUS
                ],
                "calculate": self.calculate_creditor_debt
            },
        }
        rule = garnishment_rules.get(garnishment_type_lower)
        if not rule:
            return {"error": f"Unsupported garnishment type: {garnishment_type}"}
        required_fields = rule["fields"]
        missing_fields = self.validate_fields(record, required_fields)
        if missing_fields:
            return {"error": f"Missing fields in record: {', '.join(missing_fields)}"}
        try:
            return rule["calculate"](record, config_data)
        except Exception as e:
            logger.error(f"Error in {garnishment_type} calculation: {e}")
            return {"error": f"Error calculating {garnishment_type}: {e}"}

    def _handle_insufficient_pay_garnishment(self, record, disposable_earning, total_mandatory_deduction_obj):
        """
        Helper to set insufficient pay messages and common fields.
        """
        record[CR.AGENCY] = [{CR.WITHHOLDING_AMT: [
            {CR.GARNISHMENT_AMOUNT: INSUFFICIENT_PAY}]}]
        record[CR.ER_DEDUCTION] = {
            CR.GARNISHMENT_FEES: "Garnishment fees cannot be deducted due to insufficient pay"}
        record[CR.WITHHOLDING_LIMIT_RULE] = CommonConstants.WITHHOLDING_RULE_PLACEHOLDER
        record[CR.TOTAL_MANDATORY_DEDUCTION] = round(
            total_mandatory_deduction_obj, 2)
        record[CR.DISPOSABLE_EARNING] = round(disposable_earning, 2)
        record[CR.WITHHOLDING_BASIS] = CM.NA
        record[CR.WITHHOLDING_CAP] = CM.NA
        return record

    def calculate_child_support(self, record, config_data=None):
        """
        Calculate child support garnishment.
        """
        try:
            work_state = record.get(EE.WORK_STATE)
            child_support_instance = ChildSupport(work_state)
            tcsa = child_support_instance.get_list_support_amt(record)
            is_multiple = len(tcsa) > 1
            result = (MultipleChild if is_multiple else SingleChild)(
                work_state).calculate(record)
            child_support_data = result["result_amt"]
            arrear_amount_data = result["arrear_amt"]
            ade, de, mde = result["ade"], result["de"], result["mde"]
            total_withhold_amt = sum(
                child_support_data.values()) + sum(arrear_amount_data.values())
            if total_withhold_amt <= 0:
                record.update({
                    CR.AGENCY: [
                        {CR.WITHHOLDING_AMT: [{CR.GARNISHMENT_AMOUNT: INSUFFICIENT_PAY}
                                              for _ in child_support_data]},
                        {"arrear": [{CR.WITHHOLDING_ARREAR: INSUFFICIENT_PAY}
                                    for _ in arrear_amount_data]}
                    ],
                    CR.ER_DEDUCTION: {CR.GARNISHMENT_FEES: "Garnishment fees cannot be deducted due to insufficient pay"},
                    CR.WITHHOLDING_BASIS: CM.NA,
                    CR.WITHHOLDING_CAP: CM.NA
                })
            else:
                record.update({
                    CR.AGENCY: [
                        {CR.WITHHOLDING_AMT: [{CR.GARNISHMENT_AMOUNT: amt}
                                              for amt in child_support_data.values()]},
                        {CR.ARREAR: [{CR.WITHHOLDING_ARREAR: amt}
                                     for amt in arrear_amount_data.values()]}
                    ],
                    CR.ER_DEDUCTION: {CR.GARNISHMENT_FEES: self.get_garnishment_fees(record, total_withhold_amt)},
                    CR.DISPOSABLE_EARNING: round(de, 2),
                    CR.ALLOWABLE_DISPOSABLE_EARNING: round(ade, 2),
                    CR.TOTAL_MANDATORY_DEDUCTION: round(mde, 2),
                    CR.WITHHOLDING_LIMIT_RULE: CommonConstants.WITHHOLDING_RULE_PLACEHOLDER,
                    CR.WITHHOLDING_BASIS: CM.NA,
                    CR.WITHHOLDING_CAP: CM.NA
                })
            return record
        except Exception as e:
            logger.error(f"Error calculating child support: {e}")
            return {"error": f"Error calculating child support: {e}"}

    def calculate_federal_tax(self, record, config_data=None):
        """
        Calculate federal tax garnishment.
        """
        try:
            work_state = record.get(EE.WORK_STATE)
            result = FederalTax().calculate(record)
            if result == 0:
                record[CR.AGENCY] = [
                    {CR.WITHHOLDING_AMT: [{GR.FEDERAL_TAX_LEVY: INSUFFICIENT_PAY}]}]
            else:
                record[CR.AGENCY] = [
                    {CR.WITHHOLDING_AMT: [{GR.FEDERAL_TAX_LEVY: result}]}]
            record[CR.ER_DEDUCTION] = {
                CR.GARNISHMENT_FEES: self.get_rounded_garnishment_fee(work_state, record, result)}
            record[CR.WITHHOLDING_BASIS] = CM.NA
            record[CR.WITHHOLDING_CAP] = CM.NA
            return record
        except Exception as e:
            logger.error(f"Error calculating federal tax: {e}")
            return {"error": f"Error calculating federal tax: {e}"}

    def calculate_student_loan(self, record, config_data=None):
        """
        Calculate student loan garnishment.
        """
        try:
            work_state = record.get(EE.WORK_STATE)
            result = StudentLoanCalculator().calculate(record)
            loan_amt = result["student_loan_amt"]
            if len(loan_amt) == 1:
                record[CR.AGENCY] = [{
                    CR.WITHHOLDING_AMT: [
                        {GR.STUDENT_DEFAULT_LOAN: loan_amt.values()}]}]
            else:
                record[CR.AGENCY] = [{
                    CR.WITHHOLDING_AMT: [{GR.STUDENT_DEFAULT_LOAN: amt}
                                     for amt in loan_amt.values()]}]
            total_student_loan_amt = sum(loan_amt.values())
            record[CR.ER_DEDUCTION] = {CR.GARNISHMENT_FEES: self.get_rounded_garnishment_fee(
                work_state, record, total_student_loan_amt)}
            record[CR.WITHHOLDING_BASIS] = CM.NA
            record[CR.WITHHOLDING_CAP] = CM.NA
            record[CR.DISPOSABLE_EARNING] = result[CR.DISPOSABLE_EARNING]
            return record
        except Exception as e:
            logger.error(f"Error calculating student loan: {e}")
            return {"error": f"Error calculating student loan: {e}"}

    def calculate_state_tax_levy(self, record, config_data=None):
        """
        Calculate state tax levy garnishment.
        """
        try:
            state_tax_view = StateTaxLevyCalculator()
            work_state = record.get(EE.WORK_STATE)
            result = state_tax_view.calculate(
                record, config_data[GT.STATE_TAX_LEVY])
            total_mandatory_deduction_val = ChildSupport(
                work_state).calculate_md(record)
            if result == CommonConstants.NOT_FOUND:
                return None
            if isinstance(result, dict) and result.get(CR.WITHHOLDING_AMT, 0) <= 0:
                return self._handle_insufficient_pay_garnishment(
                    record,
                    result.get(CR.DISPOSABLE_EARNING, 0),
                    total_mandatory_deduction_val
                )
            else:
                record[CR.AGENCY] = [{
                    CR.WITHHOLDING_AMT: [
                        {CR.GARNISHMENT_AMOUNT: round(
                            result[CR.WITHHOLDING_AMT], 2)}
                    ]
                }]
                record[CR.ER_DEDUCTION] = {
                    CR.GARNISHMENT_FEES: self.get_rounded_garnishment_fee(
                        work_state, record, result[CR.WITHHOLDING_AMT]
                    )
                }
                record[CR.WITHHOLDING_LIMIT_RULE] = CommonConstants.WITHHOLDING_RULE_PLACEHOLDER
                record[CR.TOTAL_MANDATORY_DEDUCTION] = round(
                    total_mandatory_deduction_val, 2)
                record[CR.DISPOSABLE_EARNING] = round(
                    result[CR.DISPOSABLE_EARNING], 2)
                record[CR.WITHHOLDING_BASIS] = result.get(CR.WITHHOLDING_BASIS)
                record[CR.WITHHOLDING_CAP] = result.get(CR.WITHHOLDING_CAP)
                return record
        except Exception as e:
            logger.error(f"Error calculating state tax levy: {e}")
            return {"error": f"Error calculating state tax levy: {e}"}

    def calculate_creditor_debt(self, record, config_data=None):
        """
        Calculate creditor debt garnishment.
        """
        try:
            creditor_debt_calculator = CreditorDebtCalculator()
            work_state = record.get(EE.WORK_STATE)
            result = creditor_debt_calculator.calculate(
                record, config_data[GT.CREDITOR_DEBT])
            if result == CommonConstants.NOT_FOUND:
                return None
            elif result == CommonConstants.NOT_PERMITTED:
                return CommonConstants.NOT_PERMITTED
            total_mandatory_deduction_val = ChildSupport(
                work_state).calculate_md(record)
            if result[CR.WITHHOLDING_AMT] <= 0:
                return self._handle_insufficient_pay_garnishment(
                    record, result[CR.DISPOSABLE_EARNING], total_mandatory_deduction_val)
            else:
                record[CR.AGENCY] = [{CR.WITHHOLDING_AMT: [
                    {CR.CREDITOR_DEBT: max(round(result[CR.WITHHOLDING_AMT], 2), 0)}]}]
                record[CR.DISPOSABLE_EARNING] = round(
                    result[CR.DISPOSABLE_EARNING], 2)
                record[CR.TOTAL_MANDATORY_DEDUCTION] = round(
                    total_mandatory_deduction_val, 2)
                record[CR.ER_DEDUCTION] = {CR.GARNISHMENT_FEES: self.get_rounded_garnishment_fee(
                    work_state, record, result[CR.WITHHOLDING_AMT])}
                record[CR.WITHHOLDING_LIMIT_RULE] = CommonConstants.WITHHOLDING_RULE_PLACEHOLDER
                record[CR.WITHHOLDING_BASIS] = result.get(CR.WITHHOLDING_BASIS)
                record[CR.WITHHOLDING_CAP] = result.get(CR.WITHHOLDING_CAP)
                return record
        except Exception as e:
            logger.error(f"Error calculating creditor debt: {e}")
            return {"error": f"Error calculating creditor debt: {e}"}

    def calculate_garnishment_wrapper(self, record, config_data):
        """
        Wrapper function for parallel processing of garnishment calculations.
        """
        try:
            garnishment_data = record.get("garnishment_data")
            if not garnishment_data:
                return None
            garnishment_type = garnishment_data[0].get(
                EE.GARNISHMENT_TYPE, "").strip().lower()
            result = self.calculate_garnishment(
                garnishment_type, record, config_data)
            if result is None:
                return CommonConstants.NOT_FOUND
            elif result == CommonConstants.NOT_PERMITTED:
                return CommonConstants.NOT_PERMITTED
            else:
                return result
        except Exception as e:
            logger.error(f"Error in garnishment wrapper: {e}")
            return {"error": f"Error in garnishment wrapper: {e}"}

    def calculate_garnishment_result(self, case_info, config_data):
        """
        Calculates garnishment result for a single case.
        """
        try:
            state = StateAbbreviations(case_info.get(
                EE.WORK_STATE)).get_state_name_and_abbr()
            ee_id = case_info.get(EE.EMPLOYEE_ID)
            calculated_result = self.calculate_garnishment_wrapper(
                case_info, config_data)
            if isinstance(calculated_result, dict) and 'error' in calculated_result:
                return {
                    "error": calculated_result["error"],
                    "status_code": calculated_result.get("status_code", 500),
                    "employee_id": ee_id,
                    "state": state
                }
            if calculated_result == CommonConstants.NOT_FOUND:
                return {
                    "error": f"Garnishment could not be calculated for employee {ee_id} because the state of {state} has not been implemented yet."
                }
            elif calculated_result == CommonConstants.NOT_PERMITTED:
                return {"error": f"In {state}, garnishment for creditor debt is not permitted."}
            elif not calculated_result:
                return {
                    "error": f"Could not calculate garnishment for employee: {ee_id}"
                }
            return calculated_result
        except Exception as e:
            logger.error(
                f"Unexpected error during garnishment calculation for employee {case_info.get(EE.EMPLOYEE_ID)}: {e}")
            return {
                "error": f"Unexpected error during garnishment calculation for employee {case_info.get(EE.EMPLOYEE_ID)}: {str(e)}"
            }

    def process_and_store_case(self, case_info, batch_id, config_data):
        try:
            with transaction.atomic():
                ee_id = case_info.get(EE.EMPLOYEE_ID)
                state = StateAbbreviations(case_info.get(
                    EE.WORK_STATE)).get_state_name_and_abbr().title()
                pay_period = case_info.get(EE.PAY_PERIOD).title()

                result = self.calculate_garnishment_result(
                    case_info, config_data)

                withholding_basis = result.get(
                    CR.WITHHOLDING_BASIS)
                withholding_cap = result.get(
                    CR.WITHHOLDING_CAP)

                if isinstance(result, dict) and result.get("error"):
                    return result

                garnishment_type_data = result.get("garnishment_data")
                if garnishment_type_data:
                    first_garnishment_type = garnishment_type_data[0].get(
                        "type").lower()
                    case_id = garnishment_type_data[0].get(
                        "data", [{}])[0].get(EE.CASE_ID)

                    if first_garnishment_type == GT.STATE_TAX_LEVY.lower():
                        try:
                            rule = state_tax_levy_rule.objects.get(
                                state__iexact=state)

                            serializer_data = StateTaxLevyConfigSerializers(
                                rule).data
                            serializer_data.update({
                                CR.WITHHOLDING_BASIS: withholding_basis,
                                CR.WITHHOLDING_CAP: withholding_cap,
                                EE.EMPLOYEE_ID: ee_id,
                                EE.PAY_PERIOD: pay_period
                            })
                            serializer_data.pop('id', None)
                            state_tax_levy_applied_rule.objects.update_or_create(
                                case_id=case_id, defaults=serializer_data)
                        except state_tax_levy_rule.DoesNotExist:
                            pass

                    elif first_garnishment_type == GT.CREDITOR_DEBT.lower():
                        data = {
                            EE.EMPLOYEE_ID: ee_id,
                            CR.WITHHOLDING_BASIS: withholding_basis,
                            EE.STATE: state,
                            CR.WITHHOLDING_CAP: withholding_cap,
                            EE.PAY_PERIOD: pay_period

                        }
                        creditor_debt_applied_rule.objects.update_or_create(
                            case_id=case_id, defaults=data)

                # Store or update Employee Data
                employee_defaults = {
                    EE.CASE_ID: case_info.get("garnishment_data", [{}])[0].get("data", [{}])[0].get(EE.CASE_ID, ""),
                    EE.WORK_STATE: case_info.get(EE.WORK_STATE),
                    EE.NO_OF_EXEMPTION_INCLUDING_SELF: case_info.get(EE.NO_OF_EXEMPTION_INCLUDING_SELF),
                    EE.PAY_PERIOD: case_info.get(EE.PAY_PERIOD),
                    EE.FILING_STATUS: case_info.get(EE.FILING_STATUS),
                    EE.AGE: case_info.get(EE.AGE),
                    EE.IS_BLIND: case_info.get(EE.IS_BLIND),
                    EE.IS_SPOUSE_BLIND: case_info.get(EE.IS_SPOUSE_BLIND),
                    EE.SPOUSE_AGE: case_info.get(EE.SPOUSE_AGE),
                    EE.SUPPORT_SECOND_FAMILY: case_info.get(EE.SUPPORT_SECOND_FAMILY),
                    EE.NO_OF_STUDENT_DEFAULT_LOAN: case_info.get(EE.NO_OF_STUDENT_DEFAULT_LOAN),
                    EE.ARREARS_GREATER_THAN_12_WEEKS: case_info.get(EE.ARREARS_GREATER_THAN_12_WEEKS),
                    EE.NO_OF_DEPENDENT_EXEMPTION: case_info.get(EE.NO_OF_DEPENDENT_EXEMPTION),
                }
                employee_batch_data.objects.update_or_create(
                    ee_id=ee_id, defaults=employee_defaults)

                # Store or update Payroll Taxes
                payroll_data = case_info.get(
                    PT.PAYROLL_TAXES, {})
                payroll_defaults = {
                    CA.WAGES: case_info.get(CA.WAGES),
                    CA.COMMISSION_AND_BONUS: case_info.get(CA.COMMISSION_AND_BONUS),
                    CA.NON_ACCOUNTABLE_ALLOWANCES: case_info.get(CA.NON_ACCOUNTABLE_ALLOWANCES),
                    CA.GROSS_PAY: case_info.get(CA.GROSS_PAY),
                    EE.DEBT: case_info.get(EE.DEBT),
                    EE.EXEMPTION_AMOUNT: case_info.get(EE.EXEMPTION_AMOUNT),
                    CA.NET_PAY: case_info.get(CA.NET_PAY),
                    PT.FEDERAL_INCOME_TAX: payroll_data.get(PT.FEDERAL_INCOME_TAX),
                    PT.SOCIAL_SECURITY_TAX: payroll_data.get(PT.SOCIAL_SECURITY_TAX),
                    PT.MEDICARE_TAX: payroll_data.get(PT.MEDICARE_TAX),
                    PT.STATE_TAX: payroll_data.get(PT.STATE_TAX),
                    PT.LOCAL_TAX: payroll_data.get(PT.LOCAL_TAX),
                    PT.UNION_DUES: payroll_data.get(PT.UNION_DUES),
                    PT.MEDICAL_INSURANCE_PRETAX: payroll_data.get(PT.MEDICAL_INSURANCE_PRETAX),
                    PT.INDUSTRIAL_INSURANCE: payroll_data.get(PT.INDUSTRIAL_INSURANCE),
                    PT.LIFE_INSURANCE: payroll_data.get(PT.LIFE_INSURANCE),
                    PT.CALIFORNIA_SDI: payroll_data.get(PT.CALIFORNIA_SDI, 0),
                }
                payroll_taxes_batch_data.objects.update_or_create(
                    ee_id=ee_id, defaults=payroll_defaults)

                # Deduplicate and prepare Garnishment Data
                unique_garnishments_to_create = {}
                for garnishment_group in case_info.get(CA.GARNISHMENT_DATA, []):
                    garnishment_type = garnishment_group.get(
                        EE.GARNISHMENT_TYPE, "")
                    for garnishment in garnishment_group.get("data", []):
                        case_id_garnish = garnishment.get(
                            EE.CASE_ID)
                        if case_id_garnish:
                            unique_garnishments_to_create[case_id_garnish] = garnishment_batch_data(
                                case_id=case_id_garnish,
                                garnishment_type=garnishment_type,
                                ordered_amount=garnishment.get(
                                    CA.ORDERED_AMOUNT),
                                arrear_amount=garnishment.get(
                                    CA.ARREAR_AMOUNT),
                                current_medical_support=garnishment.get(
                                    CA.CURRENT_MEDICAL_SUPPORT),
                                past_due_medical_support=garnishment.get(
                                    CA.PAST_DUE_MEDICAL_SUPPORT),
                                current_spousal_support=garnishment.get(
                                    CA.CURRENT_SPOUSAL_SUPPORT),
                                past_due_spousal_support=garnishment.get(
                                    CA.PAST_DUE_SPOUSAL_SUPPORT),
                                ee_id=ee_id
                            )

                if unique_garnishments_to_create:
                    garnishment_batch_data.objects.bulk_create(
                        unique_garnishments_to_create.values(),
                        update_conflicts=True,
                        unique_fields=["case_id"],
                        update_fields=[
                            "garnishment_type", "ordered_amount", "arrear_amount",
                            "current_medical_support", "past_due_medical_support",
                            "current_spousal_support", "past_due_spousal_support", "ee_id"
                        ]
                    )

                result.pop(CR.WITHHOLDING_BASIS)
                result.pop(CR.WITHHOLDING_CAP)
            return result

        except Exception as e:
            return {"error": f"Error processing case for employee {case_info.get(EE.EMPLOYEE_ID)}: {str(e)}"}


class PostCalculationView(APIView):
    """Handles Garnishment Calculation API Requests"""

    def get_all_garnishment_types(self, cases_data):
        """Extract all unique garnishment types from the cases data."""
        return {
            garnishment.get(EE.GARNISHMENT_TYPE).lower().strip()
            for case in cases_data
            for garnishment in case.get(EE.GARNISHMENT_DATA, [])
            if garnishment.get(EE.GARNISHMENT_TYPE).lower().strip()
        }

    @log_and_handle_exceptions
    def post(self, request, *args, **kwargs):
        batch_id = request.data.get(BatchDetail.BATCH_ID)
        cases_data = request.data.get("cases", [])

        if not batch_id:
            return Response({"error": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not cases_data:
            return Response({"error": "No rows provided"}, status=status.HTTP_400_BAD_REQUEST)

        output = []
        calculation_service = CalculationDataView()

        garnishment_types = self.get_all_garnishment_types(cases_data)
        config_data = calculation_service.preload_config_data(
            garnishment_types)

        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_case = {
                executor.submit(calculation_service.process_and_store_case, case_info, batch_id, config_data): case_info
                for case_info in cases_data
            }

            for future in as_completed(future_to_case):
                case_info_original = future_to_case[future]
                ee_id_for_log = case_info_original.get(
                    EE.EMPLOYEE_ID, "N/A")
                try:
                    result = future.result()
                    if result:
                        output.append(result)
                        log_api(
                            api_name="garnishment_calculate",
                            endpoint="/garnishment_calculate/",
                            status_code=200,
                            message=f"API executed successfully for employee: {ee_id_for_log}",
                            status="Success",
                            user_id=getattr(request.user, 'id', None)
                        )
                except Exception as e:
                    error_message = f"Error processing garnishment for employee {ee_id_for_log}: {e}"
                    output.append({
                        "error": error_message,
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR
                    })
                    log_api(
                        api_name="garnishment_calculate",
                        endpoint="/garnishment_calculate/",
                        status_code=500,
                        message=error_message,
                        status="Failed",
                        user_id=getattr(request.user, 'id', None)
                    )

        if all("error" in item for item in output) and output:
            return ResponseHelper.error_response(
                'Errors occurred during processing of some cases.',
                output,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({
            "success": True,
            "message": "Result Generated Successfully",
            "status_code": status.HTTP_200_OK,
            "batch_id": batch_id,
            "results": output
        }, status=status.HTTP_200_OK)
