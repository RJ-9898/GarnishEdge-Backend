from User_app.serializers import CreditorDebtExemptAmtConfigSerializers
from User_app.models import creditor_debt_exempt_amt_config
from rest_framework.response import Response
from rest_framework import status
from GarnishEdge_Project.garnishment_library import child_support as cs
from GarnishEdge_Project.garnishment_library import gar_resused_classes as gc
from GarnishEdge_Project.garnishment_library.utility_class import UtilityClass, CalculationResponse as CR
from User_app.constants import (StateList as ST,
                                FilingStatusFields, EmployeeFields, CalculationMessages as CM,
                                ExemptConfigFields as EC, CommonConstants as CC, CalculationResponseFields as CF)


class CreditorDebtHelper():
    """
    Helper class for general creditor debt logic.
    """

    def _general_debt_logic(self, disposable_earning, config_data):
        """
        Calculate the amount of disposable earnings that can be garnished for creditor debt
        using the general formula (used by multiple states).
        """
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            upper_threshold_amount = float(
                config_data[EC.UPPER_THRESHOLD_AMOUNT])
            upper_threshold_percent = float(
                config_data[EC.UPPER_THRESHOLD_PERCENT])/100
            if disposable_earning <= lower_threshold_amount:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER, CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))
            elif lower_threshold_amount <= disposable_earning <= upper_threshold_amount:
                return UtilityClass.build_response(disposable_earning - lower_threshold_amount, disposable_earning,
                                                   CM.DE_GT_LOWER_LT_UPPER, f"{CM.DISPOSABLE_EARNING} - {CM.LOWER_THRESHOLD_AMOUNT}")
            elif disposable_earning >= upper_threshold_amount:
                return UtilityClass.build_response(
                    upper_threshold_percent * disposable_earning, disposable_earning, CM.DE_GT_UPPER, f"{upper_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}")
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in _general_debt_logic: {str(e)}"
            )

    def _minimum_wage_threshold_compare(self, disposable_earning, threshold_amount, threshold_percent):
        try:
            if disposable_earning <= threshold_amount:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER, CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))
            elif disposable_earning > threshold_amount:
                diff_of_de_and_threshold_amount = disposable_earning - threshold_amount
                de_percent = disposable_earning * threshold_percent
                return UtilityClass.build_response(
                    min(diff_of_de_and_threshold_amount, de_percent), disposable_earning, CM.DE_GT_UPPER, f"Min({threshold_percent*100}% of {CM.DISPOSABLE_EARNING},({CM.DISPOSABLE_EARNING} - threshold_amount)")
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in _general_debt_logic: {str(e)}"
            )

    def _comsumer_debt_general_logic(self, disposable_earning, is_consumer_debt, non_consumer_debt, config_data):
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            upper_threshold_amount = float(
                config_data[EC.UPPER_THRESHOLD_AMOUNT])
            lower_threshold_percent = float(
                config_data[EC.LOWER_THRESHOLD_PERCENT1])/100
            upper_threshold_percent = float(
                config_data[EC.UPPER_THRESHOLD_PERCENT])/100

            if is_consumer_debt == True:
                return self._minimum_wage_threshold_compare(
                    disposable_earning, lower_threshold_amount, lower_threshold_percent)
            elif non_consumer_debt == True:
                return self._minimum_wage_threshold_compare(
                    disposable_earning, upper_threshold_amount, upper_threshold_percent)
            else:
                return UtilityClass.build_response(
                    0, disposable_earning, "ERROR",
                    f"Exception in _comsumer_debt_general_logic: {str(e)}"
                )
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in _comsumer_debt_general_logic: {str(e)}"
            )


class StateWiseCreditorDebtFormulas(CreditorDebtHelper):
    """
    Contains state-specific creditor debt calculation formulas.
    Each method implements the logic for a particular state.
    """

    def cal_arizona_creditor_debt(self, disposable_earning, config_data):
        """
        Arizona: Garnishment calculation based on lower threshold and percent.
        """
        try:
            lower_threshold_percent = float(
                config_data[EC.LOWER_THRESHOLD_PERCENT1])/100
            ten_percent_of_de = lower_threshold_percent * disposable_earning
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])

            if disposable_earning <= lower_threshold_amount:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER, CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))
            else:
                diff_of_de_and_product_of_smw_and_times = disposable_earning-lower_threshold_amount

                withholding_amt = min(
                    diff_of_de_and_product_of_smw_and_times, ten_percent_of_de)
                return UtilityClass.build_response(
                    withholding_amt,  disposable_earning, CM.DE_LE_LOWER, f"Min({CM.DISPOSABLE_EARNING} - {CM.LOWER_THRESHOLD_AMOUNT},{lower_threshold_percent*100} of {CM.DISPOSABLE_EARNING}))")
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_arizona_creditor_debt: {str(e)}"
            )

    def cal_delaware_creditor_debt(self, disposable_earning, config_data):
        """
        Delaware: Garnishment calculation based on deducted basis percent.
        """
        try:
            deducted_basis_percent = float(
                config_data[EC.DEDUCTED_BASIS_PERCENT]) / 100
            withholding_amt = disposable_earning * deducted_basis_percent

            return UtilityClass.build_response(
                withholding_amt, disposable_earning, "NA",
                f"{deducted_basis_percent*100}% of {CM.DISPOSABLE_EARNING}"
            )
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_delaware_creditor_debt: {str(e)}"
            )

    def cal_hawaii_creditor_debt(self, disposable_earning, config_data):
        """
        Hawaii: Garnishment calculation based on weekly to monthly conversion.
        """

        try:
            # calculating the disposable earning for monthly basis
            mde = disposable_earning*52/12

            if disposable_earning >= 200:
                de_five_percent = 0.05*100
                de_ten_percent = 0.10*100
                rmde = mde-200
                de_twenty_percent = 0.20*rmde
                mde_total = de_five_percent+de_ten_percent+de_twenty_percent
                wa = mde_total*12/52

                general_debt_logic = self._general_debt_logic(
                    disposable_earning, config_data)

                withholding_amt = general_debt_logic[CF.WITHHOLDING_AMT]
                withholding_cap = general_debt_logic[CF.WITHHOLDING_CAP]

                lesser_amt = min(wa, withholding_amt)
                return UtilityClass.build_response(lesser_amt, disposable_earning,
                                                   f"{CM.DISPOSABLE_EARNING} >= 200",
                                                   f"Min({CM.WITHHOLDING_AMT},{withholding_cap})")
            else:
                return UtilityClass.build_response(0, disposable_earning,
                                                   "de < 200",
                                                   CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_hawaii_creditor_debt: {str(e)}"
            )

    def cal_new_jersey_creditor_debt(self, gross_pay, config_data):
        """
        New Jersey: Garnishment calculation based on deducted basis percent of gross pay.
        """
        try:
            deducted_basis_percent = float(
                config_data[EC.DEDUCTED_BASIS_PERCENT]) / 100
            return UtilityClass.build_response(
                gross_pay * deducted_basis_percent, 0, "NA",
                f"{deducted_basis_percent*100}% of gross pay"
            )
        except Exception as e:
            return UtilityClass.build_response(
                0, 0, "ERROR",
                f"Exception in cal_new_jersey_creditor_debt: {str(e)}"
            )

    def cal_maine_creditor_debt(self, disposable_earning, config_data):
        """
        Maine: Garnishment calculation with lower and upper thresholds.
        """
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            upper_threshold_amount = float(
                config_data[EC.UPPER_THRESHOLD_AMOUNT])
            upper_threshold_percent = float(
                config_data[EC.UPPER_THRESHOLD_PERCENT]) / 100

            if disposable_earning <= lower_threshold_amount:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER,
                    CR.get_zero_withholding_response(
                        CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT)
                )
            elif lower_threshold_amount <= disposable_earning <= upper_threshold_amount:
                diff = disposable_earning - lower_threshold_amount
                return UtilityClass.build_response(
                    diff, disposable_earning, CM.DE_GT_LOWER_LT_UPPER,
                    f"{CM.DISPOSABLE_EARNING} - {CM.LOWER_THRESHOLD_AMOUNT}"
                )
            elif disposable_earning >= upper_threshold_amount:
                return UtilityClass.build_response(
                    disposable_earning * upper_threshold_percent, disposable_earning,
                    CM.DE_GT_UPPER, f"{upper_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}"
                )
            else:
                return UtilityClass.build_response(
                    0, disposable_earning, "ERROR",
                    "Unhandled case in cal_maine_creditor_debt"
                )
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_maine_creditor_debt: {str(e)}"
            )

    def cal_missouri_creditor_debt(self, disposable_earning, filing_status, config_data):
        """
        Missouri: Garnishment calculation based on filing status.
        """
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            upper_threshold_amount = float(
                config_data[EC.UPPER_THRESHOLD_AMOUNT])
            filing_status_percent = float(
                config_data[EC.FILING_STATUS_PERCENT]) / 100

            if filing_status == FilingStatusFields.HEAD_OF_HOUSEHOLD:
                if disposable_earning <= lower_threshold_amount:
                    return UtilityClass.build_response(0, disposable_earning,
                                                       CM.DE_LE_LOWER,
                                                       CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))
                elif lower_threshold_amount <= disposable_earning <= upper_threshold_amount:
                    return UtilityClass.build_response(upper_threshold_amount - disposable_earning, disposable_earning,
                                                       CM.DE_GT_LOWER_LT_UPPER,
                                                       f"{CM.DISPOSABLE_EARNING} - {CM.UPPER_THRESHOLD_AMOUNT}")
                elif disposable_earning >= upper_threshold_amount:
                    return UtilityClass.build_response(filing_status_percent * disposable_earning, disposable_earning,
                                                       CM.DE_GT_UPPER,
                                                       f"{filing_status_percent * 100}% of {CM.DISPOSABLE_EARNING}")
            else:
                withholding_amt = self._general_debt_logic(
                    disposable_earning, config_data)
                return UtilityClass.build_response(withholding_amt[CF.WITHHOLDING_AMT], disposable_earning, withholding_amt[CF.WITHHOLDING_BASIS], withholding_amt[CF.WITHHOLDING_CAP])

        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_missouri_creditor_debt: {str(e)}"
            )

    def cal_nebraska_creditor_debt(self, disposable_earning, filing_status, config_data):
        """
        Nebraska: Garnishment calculation based on filing status.
        """
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            upper_threshold_amount = float(
                config_data[EC.UPPER_THRESHOLD_AMOUNT])
            filing_status_percent = float(
                config_data[EC.FILING_STATUS_PERCENT]) / 100

            if filing_status == FilingStatusFields.HEAD_OF_HOUSEHOLD:
                if disposable_earning <= lower_threshold_amount:
                    withholding_amt = UtilityClass.build_response(
                        0, disposable_earning, CM.DE_LE_LOWER, CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))

                elif lower_threshold_amount <= disposable_earning <= upper_threshold_amount:
                    withholding_amt = UtilityClass.build_response(disposable_earning-lower_threshold_amount, disposable_earning,
                                                                  CM.DE_GT_LOWER_LT_UPPER, f"{CM.UPPER_THRESHOLD_AMOUNT} - {CM.DISPOSABLE_EARNING}")
                elif disposable_earning >= upper_threshold_amount:
                    withholding_amt = UtilityClass.build_response(
                        filing_status_percent * disposable_earning, disposable_earning, CM.DE_GT_UPPER, f"{filing_status_percent * 100}% of {CM.DISPOSABLE_EARNING}")
                return withholding_amt
            else:
                withholding_amt = self._general_debt_logic(
                    disposable_earning, config_data)
                return UtilityClass.build_response(withholding_amt[CF.WITHHOLDING_AMT], disposable_earning, withholding_amt[CF.WITHHOLDING_BASIS], withholding_amt[CF.WITHHOLDING_CAP])

        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_nebraska_creditor_debt: {str(e)}"
            )

    def cal_north_dakota(self, disposable_earning, no_of_exemption_including_self, config_data):
        """
        North Dakota: Garnishment calculation based on exemption count.
        """
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            exempt_amt = float(config_data[EC.EXEMPT_AMOUNT])
            lower_threshold_percent = float(
                config_data[EC.LOWER_THRESHOLD_PERCENT1]) / 100

            if disposable_earning <= lower_threshold_amount:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER, CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))

            else:  # disposable_earning > lower_threshold_amount
                if no_of_exemption_including_self == 1:
                    diff_of_de_and_lower_threshold_amount = disposable_earning-lower_threshold_amount
                    de_percent = disposable_earning*lower_threshold_percent
                    return UtilityClass.build_response(
                        min(diff_of_de_and_lower_threshold_amount, de_percent), disposable_earning, CM.DE_GT_LOWER, f"Min({lower_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}, {CM.DISPOSABLE_EARNING} - {CM.LOWER_THRESHOLD_AMOUNT})")
                elif no_of_exemption_including_self > 1:
                    dependent_exemption = exempt_amt * \
                        (no_of_exemption_including_self-1)
                    total_exempt_amt = lower_threshold_amount+dependent_exemption
                    diff_between_de_and_exempt_amt = disposable_earning-total_exempt_amt
                    return UtilityClass.build_response(
                        min(
                            diff_between_de_and_exempt_amt, .20*disposable_earning), disposable_earning, CM.DE_GT_LOWER, f"Min({lower_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}, {CM.DISPOSABLE_EARNING} - ({CM.LOWER_THRESHOLD_AMOUNT} + ({CM.LOWER_THRESHOLD_AMOUNT}+dependent_exemption)))")

        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_north_dakota: {str(e)}"
            )

    def cal_tennessee_creditor_debt(self, disposable_earning, no_of_dependent_child, config_data):
        """
        washington: Garnishment calculation based on disposable_earning and no_of_dependent_child.
        """
        try:

            exempt_amt = float(config_data[EC.EXEMPT_AMOUNT])
            general_result = self._general_debt_logic(
                disposable_earning, config_data)
            if no_of_dependent_child == 0:
                return UtilityClass.build_response(general_result[CF.WITHHOLDING_AMT], disposable_earning,
                                                   general_result[CF.WITHHOLDING_BASIS], f"{general_result[CF.WITHHOLDING_CAP]}")
            else:
                exempt_amt_for_dependent = exempt_amt*no_of_dependent_child
                withholding_amt = general_result[CF.WITHHOLDING_AMT] - \
                    exempt_amt_for_dependent
                return UtilityClass.build_response(withholding_amt, disposable_earning,
                                                   general_result[CF.WITHHOLDING_BASIS], f"{general_result[CF.WITHHOLDING_CAP]}-Exempt Amount for Dependent")
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_tennessee_creditor_debt: {str(e)}"
            )

    def cal_nevada_creditor_debt(self, gross_pay, disposable_earning, config_data, percent1=.18):
        """
        Nevada: Garnishment calculation based on lower threshold and percent.
        """
        try:
            wl_limit_threshold = 770
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            lower_threshold_percent = float(
                config_data[EC.LOWER_THRESHOLD_PERCENT1]) / 100

            if gross_pay <= wl_limit_threshold:
                withholding_amt = disposable_earning*percent1
                return UtilityClass.build_response(withholding_amt, disposable_earning,
                                                   f"{CM.GROSS_PAY} <= {wl_limit_threshold}", f"{percent1*100}% of {CM.DISPOSABLE_EARNING}")
            else:  # disposable_earning > lower_threshold_amount
                diff_of_de_and_fmw_fifty_times = disposable_earning-lower_threshold_amount
                twenty_five_percent_of_de = disposable_earning*lower_threshold_percent
                withholding_amt = min(
                    diff_of_de_and_fmw_fifty_times, twenty_five_percent_of_de)
                return UtilityClass.build_response(withholding_amt, disposable_earning,
                                                   CM.DE_GT_LOWER,
                                                   f"Min(({CM.DISPOSABLE_EARNING}-{CM.LOWER_THRESHOLD_AMOUNT}),{lower_threshold_percent*100}% of {CM.DISPOSABLE_EARNING})")
        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_nevada_creditor_debt: {str(e)}"
            )

    def cal_minnesota_creditor_debt(self, disposable_earning, config_data):
        """
        Minnesota: Garnishment calculation based on lower threshold and percent,mid threshold and percent,upper threshold and percent.
        """
        try:
            lower_threshold_amount = float(
                config_data[EC.LOWER_THRESHOLD_AMOUNT])
            mid_threshold_amount = float(
                config_data[EC.MID_THRESHOLD_AMOUNT])
            de_range_lower_to_mid_threshold_percent = float(
                config_data[EC.DE_RANGE_LOWER_TO_MID_THRESHOLD_PERCENT]) / 100
            de_range_mid_to_upper_threshold_percent = float(
                config_data[EC.DE_RANGE_MID_TO_UPPER_THRESHOLD_PERCENT]) / 100
            upper_threshold_amount = float(
                config_data[EC.UPPER_THRESHOLD_AMOUNT])
            upper_threshold_percent = float(
                config_data[EC.UPPER_THRESHOLD_PERCENT]) / 100
            if disposable_earning <= lower_threshold_amount:
                return UtilityClass.build_response(
                    0, disposable_earning, CM.DE_LE_LOWER, CR.get_zero_withholding_response(CM.DISPOSABLE_EARNING, CM.LOWER_THRESHOLD_AMOUNT))
            elif disposable_earning >= lower_threshold_amount and disposable_earning <= mid_threshold_amount:
                return UtilityClass.build_response(
                    de_range_lower_to_mid_threshold_percent*disposable_earning, disposable_earning, f"{CM.DISPOSABLE_EARNING} > {CM.LOWER_THRESHOLD_AMOUNT} and {CM.DISPOSABLE_EARNING} <= {CM.MID_THRESHOLD_AMOUNT}", f"{de_range_lower_to_mid_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}")
            elif disposable_earning >= mid_threshold_amount and disposable_earning <= upper_threshold_amount:
                return UtilityClass.build_response(
                    de_range_mid_to_upper_threshold_percent*disposable_earning, disposable_earning, f"{CM.DISPOSABLE_EARNING} > {CM.MID_THRESHOLD_AMOUNT} and {CM.DISPOSABLE_EARNING} <= {CM.UPPER_THRESHOLD_AMOUNT}", f"{de_range_mid_to_upper_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}")
            elif disposable_earning >= upper_threshold_amount:
                return UtilityClass.build_response(
                    upper_threshold_percent*disposable_earning, disposable_earning, CM.DE_GT_UPPER, f"{upper_threshold_percent*100}% of {CM.DISPOSABLE_EARNING}")

        except Exception as e:
            return UtilityClass.build_response(
                0, disposable_earning, "ERROR",
                f"Exception in cal_minnesota_creditor_debt: {str(e)}"
            )


class CreditorDebtCalculator(StateWiseCreditorDebtFormulas):

    def calculate(self, record, config_data):
        """
        Main entry point for creditor debt calculation.
        Determines the state and applies the appropriate formula.
        """
        pay_period = record.get(EmployeeFields.PAY_PERIOD).lower()
        gross_pay = record.get(EmployeeFields.GROSS_PAY)
        no_of_exemption_including_self = record.get(
            EmployeeFields.NO_OF_EXEMPTION_INCLUDING_SELF)
        state = gc.StateAbbreviations(record.get(
            EmployeeFields.WORK_STATE)).get_state_name_and_abbr()
        no_of_dependent_child = record.get(
            EmployeeFields.NO_OF_DEPENDENT_CHILD)
        filing_status = record.get(EmployeeFields.FILING_STATUS).lower()
        is_consumer_debt = record.get(EmployeeFields.IS_CONSUMER_DEBT)
        non_consumer_debt = record.get(EmployeeFields.NON_CONSUMER_DEBT)
        disposable_earning = cs.ChildSupport(state).calculate_de(record)

        def get_exempt_amt_config_data(config_data, state, pay_period):
            """
                Helper to fetch the correct config for the state and pay period.
            """

            return next(
                (
                    i
                    for i in config_data
                    if i[EmployeeFields.STATE].lower() == state.lower() and i[EmployeeFields.PAY_PERIOD].lower() == pay_period.lower()
                ), None
            )

        exempt_amt_config = get_exempt_amt_config_data(
            config_data, state, pay_period)

        try:
            state_formulas = {
                ST.ARIZONA: lambda: self.cal_arizona_creditor_debt(disposable_earning, exempt_amt_config),
                ST.DELAWARE: lambda: self.cal_delaware_creditor_debt(disposable_earning, exempt_amt_config),
                ST.HAWAII: lambda: self.cal_hawaii_creditor_debt(disposable_earning, exempt_amt_config),
                ST.MAINE: lambda: self.cal_maine_creditor_debt(disposable_earning, exempt_amt_config),
                ST.NORTH_DAKOTA: lambda: self.cal_north_dakota(disposable_earning, no_of_exemption_including_self, exempt_amt_config),
                ST.SOUTH_DAKOTA: lambda: self.cal_north_dakota(disposable_earning, no_of_exemption_including_self, exempt_amt_config),
                ST.MISSOURI: lambda: self.cal_missouri_creditor_debt(disposable_earning, filing_status, exempt_amt_config),
                ST.NEBRASKA: lambda: self.cal_nebraska_creditor_debt(disposable_earning, filing_status, exempt_amt_config),
                ST.TENNESSEE: lambda: self.cal_tennessee_creditor_debt(disposable_earning, no_of_dependent_child, exempt_amt_config),
                ST.NEW_JERSEY: lambda: self.cal_new_jersey_creditor_debt(gross_pay, exempt_amt_config),
                ST.NEVADA: lambda: self.cal_nevada_creditor_debt(gross_pay, disposable_earning, exempt_amt_config),
                ST.MINNESOTA: lambda: self.cal_minnesota_creditor_debt(
                    disposable_earning, exempt_amt_config)
            }
            formula_func = state_formulas.get(state.lower().strip())

            if formula_func:
                result = formula_func()

            else:
                _general_debt_logic = [
                    ST.ALABAMA, ST.ARKANSAS, ST.FLORIDA, ST.IDAHO, ST.MARYLAND,
                    ST.INDIANA, ST.KANSAS, ST.KENTUCKY, ST.LOUISIANA,
                    ST.MICHIGAN, ST.MISSISSIPPI, ST.MONTANA, ST.NEW_HAMPSHIRE,
                    ST.OHIO, ST.OKLAHOMA, ST.RHODE_ISLAND, ST.UTAH,
                    ST.VERMONT, ST.WYOMING, ST.GEORGIA, ST.CALIFORNIA, ST.COLORADO
                ]
                _comsumer_debt_general_logic = [
                    ST.IOWA, ST.WASHINGTON]

                _minimum_wage_threshold_compare_de = [
                    ST.ILLINOIS, ST.CONNECTICUT, ST.NEW_MEXICO, ST.VIRGINIA, ST.WEST_VIRGINIA, ST.WISCONSIN]

                _minimum_wage_threshold_compare_gp = [
                    ST.NEW_YORK, ST.MASSACHUSETTS]

                if state in [ST.TEXAS, ST.NORTH_CAROLINA, ST.SOUTH_CAROLINA]:
                    result = CC.NOT_PERMITTED
                elif state in _general_debt_logic:
                    result = self._general_debt_logic(
                        disposable_earning, exempt_amt_config)
                elif state in _comsumer_debt_general_logic:
                    result = self._comsumer_debt_general_logic(
                        disposable_earning, is_consumer_debt, non_consumer_debt, config_data)
                elif state in _minimum_wage_threshold_compare_de:
                    result = self._minimum_wage_threshold_compare(
                        disposable_earning, float(
                            exempt_amt_config[EC.LOWER_THRESHOLD_AMOUNT]), float(
                            exempt_amt_config[EC.LOWER_THRESHOLD_PERCENT1])/100),
                elif state in _minimum_wage_threshold_compare_gp:
                    result = self._minimum_wage_threshold_compare(
                        gross_pay, float(
                            exempt_amt_config[EC.LOWER_THRESHOLD_AMOUNT]), float(
                            exempt_amt_config[EC.LOWER_THRESHOLD_PERCENT1])/100),
                else:
                    result = CC.NOT_FOUND
            return result
        except Exception as e:
            return Response(
                {
                    "error": f"Exception in CreditorDebtCalculator.calculate: {str(e)}",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                }
            )
