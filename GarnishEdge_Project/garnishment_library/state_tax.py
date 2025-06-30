import logging
from User_app.models import state_tax_levy_rule
from rest_framework.response import Response
from rest_framework import status
from GarnishEdge_Project.garnishment_library import child_support as cs
from User_app.constants import (
    EmployeeFields, PayrollTaxesFields, CalculationFields, StateList, StateTaxLevyCalculationData
)
from GarnishEdge_Project.garnishment_library import gar_resused_classes as gc
from GarnishEdge_Project.garnishment_library.utility_class import UtilityClass, CalculationResponse
from User_app.constants import GarnishmentConstants as GC
from User_app.constants import CalculationMessages as CM
from User_app.constants import CommonConstants as CC
from User_app.constants import ExemptConfigFields as EC

logger = logging.getLogger(__name__)


class StateTaxViewHelper:
    """
    Helper class for state tax levy calculations.
    """

    def cal_x_disposible_income(self, gross_pay, percent=0.25):
        """
        Calculate disposable income based on gross pay and percentage.
        """
        try:
            disposable_earnings = round(gross_pay, 2)
            monthly_garnishment_amount = disposable_earnings * percent
            return monthly_garnishment_amount
        except Exception as e:
            logger.error(f"Error calculating disposable income: {e}")
            return 0

    def fmv_threshold(self):
        """
        Set Fair Market Value thresholds for calculations.
        """
        self.lower_threshold_amount = StateTaxLevyCalculationData.FMW * GC.VALUE1
        self.upper_threshold_amount = StateTaxLevyCalculationData.FMW * GC.VALUE2
        self.threshold_53 = StateTaxLevyCalculationData.FMW * GC.VALUE3

    def get_wl_percent(self, state):
        """
        Get withholding limit percent and deduction basis for a state.
        """
        try:
            state = state.strip()
            obj = state_tax_levy_rule.objects.filter(state__iexact=state)
            if obj.exists():
                return {
                    "wl_percent": obj[0].withholding_limit,
                    "deduct_from": obj[0].deduction_basis
                }
            return CC.NOT_FOUND
        except Exception as e:
            logger.error(
                f"Error fetching withholding percent for state {state}: {e}")
            return CC.NOT_FOUND

    def get_deduct_from(self, state):
        """
        Get deduction basis for a state.
        """
        try:
            state = state.title()
            obj = state_tax_levy_rule.objects.filter(state=state)
            if obj.exists():
                return obj[0].deduction_basis
            return CC.NOT_FOUND
        except Exception as e:
            logger.error(
                f"Error fetching deduction basis for state {state}: {e}")
            return CC.NOT_FOUND

    def apply_general_debt_logic(self, disposable_earning, config_data, percent=GC.DEFAULT_PERCENT):
        """
        General logic for states using lower/upper threshold and percent.
        """
        try:
            lower = float(config_data[EC.LOWER_THRESHOLD_AMOUNT])
            upper = float(config_data[EC.UPPER_THRESHOLD_AMOUNT])

            if disposable_earning <= lower:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CalculationResponse.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT)
                )
            elif lower <= disposable_earning <= upper:
                return UtilityClass.build_response(
                    disposable_earning - lower, disposable_earning,
                    CM.DE_GT_LOWER_LT_UPPER,
                    f"{CM.DISPOSABLE_EARNING} - {CM.UPPER_THRESHOLD_AMOUNT}"
                )
            return UtilityClass.build_response(
                percent * disposable_earning, disposable_earning,
                CM.DE_GT_UPPER, f"{percent * 100}% of {CM.DISPOSABLE_EARNING}"
            )
        except Exception as e:
            logger.error(f"Error in general debt logic: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))


class StateWiseStateTaxLevyFormulas(StateTaxViewHelper):
    """
    State-specific formulas for state tax levy calculations.
    """

    def cal_massachusetts(self, disposable_earning, gross_pay, config_data, percent=GC.MASSACHUSETTS_PERCENT):
        try:
            lower = float(config_data[EC.LOWER_THRESHOLD_AMOUNT])
            if disposable_earning <= lower:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CalculationResponse.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT)
                )
            diff = disposable_earning - lower
            gp_percent = gross_pay * percent
            return UtilityClass.build_response(
                min(diff, gp_percent), disposable_earning,
                CM.DE_GT_LOWER,
                f"Min({percent * 100}% of {CM.GROSS_PAY}, ({CM.DISPOSABLE_EARNING} - {CM.LOWER_THRESHOLD_AMOUNT}))"
            )
        except Exception as e:
            logger.error(f"Error in Massachusetts formula: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))

    def cal_arizona(self, disposable_earning, config_data, percent=GC.ARIZONA_PERCENT):
        try:
            lower = float(config_data[EC.LOWER_THRESHOLD_AMOUNT])
            if disposable_earning <= lower:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CalculationResponse.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT)
                )
            diff = disposable_earning - lower
            de_percent = percent * disposable_earning
            return UtilityClass.build_response(
                min(diff, de_percent), disposable_earning,
                CM.DE_GT_LOWER,
                f"Min(({CM.DISPOSABLE_EARNING}-{CM.UPPER_THRESHOLD_AMOUNT}),{percent * 100}% of {CM.DISPOSABLE_EARNING})"
            )
        except Exception as e:
            logger.error(f"Error in Arizona formula: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))

    def cal_minnesota(self, disposable_earning, config_data, percent=GC.DEFAULT_PERCENT):
        try:
            upper = float(config_data[EC.UPPER_THRESHOLD_AMOUNT])
            if disposable_earning <= upper:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CalculationResponse.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.UPPER_THRESHOLD_AMOUNT)
                )
            diff = disposable_earning - upper
            de_percent = disposable_earning * percent
            return UtilityClass.build_response(
                min(de_percent, diff), disposable_earning,
                CM.DE_GT_UPPER,
                f"Min(({CM.DISPOSABLE_EARNING}-{CM.UPPER_THRESHOLD_AMOUNT}), {percent * 100}% of {CM.DISPOSABLE_EARNING})"
            )
        except Exception as e:
            logger.error(f"Error in Minnesota formula: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))

    def cal_newyork(self, disposable_earning, gross_pay, config_data,
                    percent1=GC.NEWYORK_PERCENT1, percent2=GC.NEWYORK_PERCENT2):
        try:
            lower = float(config_data[EC.LOWER_THRESHOLD_AMOUNT])
            if disposable_earning <= lower:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CalculationResponse.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT)
                )
            de_percent = disposable_earning * percent2
            gp_percent = gross_pay * percent1
            return UtilityClass.build_response(
                min(de_percent, gp_percent), disposable_earning,
                CM.DE_GT_LOWER,
                f"Min({percent1 * 100}% of {CM.GROSS_PAY}, {percent2 * 100}% of {CM.DISPOSABLE_EARNING})"
            )
        except Exception as e:
            logger.error(f"Error in New York formula: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))

    def cal_west_virginia(self, no_of_exemption_including_self, net_pay, config_data):
        try:
            exempt_amt = GC.EXEMPT_AMOUNT
            lower = float(config_data[EC.LOWER_THRESHOLD_AMOUNT])

            if no_of_exemption_including_self == 1:
                return UtilityClass.build_response(
                    lower, 0, CM.NO_OF_EXEMPTIONS_ONE,
                    CM.LOWER_THRESHOLD_AMOUNT
                )
            exempt_amt_cal = lower + \
                (exempt_amt * (no_of_exemption_including_self - 1))
            diff = net_pay - exempt_amt_cal
            return UtilityClass.build_response(
                diff, 0, CM.NO_OF_EXEMPTIONS_MORE,
                f"{EmployeeFields.NET_PAY}-({CM.LOWER_THRESHOLD_AMOUNT}+{exempt_amt}*({CM.NO_OF_EXEMPTIONS_ONE}))"
            )
        except Exception as e:
            logger.error(f"Error in West Virginia formula: {e}")
            return UtilityClass.build_response(0, net_pay, "ERROR", str(e))

    def cal_new_mexico(self, disposable_earning, config_data, percent=GC.DEFAULT_PERCENT):
        try:
            upper = float(config_data[EC.UPPER_THRESHOLD_AMOUNT])
            if disposable_earning <= upper:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CalculationResponse.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.UPPER_THRESHOLD_AMOUNT)
                )
            diff = disposable_earning - upper
            de_percent = disposable_earning * percent
            return UtilityClass.build_response(
                min(de_percent, diff), disposable_earning,
                CM.DE_GT_UPPER,
                f"Min(({CM.DISPOSABLE_EARNING}-{CM.UPPER_THRESHOLD_AMOUNT}),{percent * 100}% of {CM.DISPOSABLE_EARNING})"
            )
        except Exception as e:
            logger.error(f"Error in New Mexico formula: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))

    def cal_delaware(self, disposable_earning, percent):
        try:
            return UtilityClass.build_response(
                disposable_earning * percent, disposable_earning,
                CM.NA, f"{percent * 100}% of {CM.DISPOSABLE_EARNING}"
            )
        except Exception as e:
            logger.error(f"Error in Delaware formula: {e}")
            return UtilityClass.build_response(0, disposable_earning, "ERROR", str(e))


class StateTaxLevyCalculator(StateWiseStateTaxLevyFormulas):
    """
    Main calculator for state tax levy, dispatching to state-specific logic.
    """

    def calculate(self, record, config_data):
        try:
            # Extract and validate required fields
            gross_pay = record.get(EmployeeFields.GROSS_PAY, 0)
            disposable_earning = cs.ChildSupport(record.get(
                EmployeeFields.WORK_STATE)).calculate_de(record)
            pay_period = record.get(EmployeeFields.PAY_PERIOD, "").lower()
            state = gc.StateAbbreviations(record.get(
                EmployeeFields.WORK_STATE, "")).get_state_name_and_abbr()
            payroll_taxes = record.get(PayrollTaxesFields.PAYROLL_TAXES, {})
            no_of_exemption_including_self = record.get(
                EmployeeFields.NO_OF_EXEMPTION_INCLUDING_SELF, 1)
            net_pay = record.get(EmployeeFields.NET_PAY, 0)
            medical_insurance = payroll_taxes.get(
                CalculationFields.MEDICAL_INSURANCE, 0)

            # Helper to get exempt amount config for state and pay period
            def get_exempt_amt_config_data(config_data, state, pay_period):
                try:
                    return next(
                        i for i in config_data
                        if i[EmployeeFields.STATE].lower() == state.lower() and i[EmployeeFields.PAY_PERIOD].lower() == pay_period.lower()
                    )
                except StopIteration:
                    logger.error(
                        f"Exempt amount config not found for state '{state}' and pay period '{pay_period}'")
                    return None

            exempt_amt_config = get_exempt_amt_config_data(
                config_data, state, pay_period)

            # Helper to get percent for state
            def percent():
                wl = self.get_wl_percent(state.strip())
                try:
                    return round(float(wl["wl_percent"]) / 100, 2) if wl and "wl_percent" in wl else 0.25
                except Exception as e:
                    logger.error(
                        f"Error parsing percent for state {state}: {e}")
                    return 0.25

            # State-specific formula dispatch
            state_formulas = {
                StateList.ARIZONA: lambda: self.cal_arizona(disposable_earning, exempt_amt_config, percent()),
                StateList.IDAHO: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.GEORGIA: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.COLORADO: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.ILLINOIS: lambda: UtilityClass.build_response(self.cal_x_disposible_income(gross_pay, percent()), 0, "NA", f"{percent() * 100}% of {CM.GROSS_PAY}"),
                StateList.MARYLAND: lambda: UtilityClass.build_response(self.cal_x_disposible_income(disposable_earning, percent()) - medical_insurance, disposable_earning, "NA", f"{percent() * 100}% of {CM.DISPOSABLE_EARNING}"),
                StateList.MASSACHUSETTS: lambda: self.cal_massachusetts(disposable_earning, gross_pay, exempt_amt_config, percent()),
                StateList.MISSOURI: lambda: UtilityClass.build_response(self.cal_x_disposible_income(disposable_earning, percent()), disposable_earning, "NA", f"{percent() * 100}% of {CM.DISPOSABLE_EARNING}"),
                StateList.NEW_JERSEY: lambda: UtilityClass.build_response(self.cal_x_disposible_income(gross_pay, percent()), 0, "NA", f"{percent() * 100}% of {CM.GROSS_PAY}"),
                StateList.MAINE: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.INDIANA: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.MINNESOTA: lambda: self.cal_minnesota(disposable_earning, exempt_amt_config, percent()),
                StateList.NEW_YORK: lambda: self.cal_newyork(disposable_earning, gross_pay, exempt_amt_config, percent()),
                StateList.NORTH_CAROLINA: lambda: UtilityClass.build_response(self.cal_x_disposible_income(gross_pay, percent()), 0, "NA", f"{percent() * 100}% of  {CM.GROSS_PAY}"),
                StateList.PENNSYLVANIA: lambda: UtilityClass.build_response(self.cal_x_disposible_income(gross_pay, percent()), 0, "NA", f"{percent() * 100}% of  {CM.GROSS_PAY}"),
                StateList.VERMONT: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.VIRGINIA: lambda: UtilityClass.build_response(self.cal_x_disposible_income(disposable_earning, percent()), disposable_earning, "NA", f"{percent() * 100}% of {CM.DISPOSABLE_EARNING}"),
                StateList.DELAWARE: lambda: self.cal_delaware(disposable_earning, percent()),
                StateList.IOWA: lambda: self.apply_general_debt_logic(disposable_earning, exempt_amt_config, percent()),
                StateList.WISCONSIN: lambda: UtilityClass.build_response(self.cal_x_disposible_income(gross_pay, percent()), 0, "NA", f"{percent() * 100}% of {CM.GROSS_PAY}"),
                StateList.WEST_VIRGINIA: lambda: self.cal_west_virginia(no_of_exemption_including_self, net_pay, exempt_amt_config),
                StateList.NEW_MEXICO: lambda: self.cal_new_mexico(
                    disposable_earning, exempt_amt_config, percent())
            }

            formula_func = state_formulas.get(state.lower())
            if formula_func:
                return formula_func()

            # Handle states with a flat 25% group
            twenty_five_percentage_grp_state = [
                StateList.ARKANSAS, StateList.KENTUCKY, StateList.OREGON,
                StateList.UTAH, StateList.CALIFORNIA, StateList.MONTANA,
                StateList.COLORADO, StateList.CONNECTICUT, StateList.LOUISIANA,
                StateList.MISSISSIPPI,
            ]
            if state in twenty_five_percentage_grp_state:
                result = self.cal_x_disposible_income(
                    disposable_earning, percent())
                return UtilityClass.build_response(result, disposable_earning, "NA", f"{percent() * 100}% of {CM.DISPOSABLE_EARNING}")
            elif state in [StateList.ALABAMA, StateList.HAWAII]:
                result = self.cal_x_disposible_income(gross_pay, percent())
                return UtilityClass.build_response(result, 0, "NA", f"{percent() * 100}% of {CM.GROSS_PAY}")

            logger.warning(f"No formula found for state: {state}")
            return CC.NOT_FOUND

        except Exception as e:
            logger.error(f"Error in state tax levy calculation: {e}")
            return Response(
                {
                    "error": str(e),
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                }
            )
