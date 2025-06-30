import os
import json
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from User_app.constants import PayPeriodFields, EmployeeFields
from ..garnishment_library.child_support import ChildSupport
from GarnishEdge_Project.garnishment_library import gar_resused_classes as gc


class StudentLoan:
    """
    Handles calculation of Student Loan garnishment amounts based on federal and state rules.
    """

    FMW_RATE = 7.25
    DEDUCTION_RATE_SINGLE_1 = 0.15
    DEDUCTION_RATE_SINGLE_2 = 0.25
    DEDUCTION_RATE_MULTI_1 = 0.15
    DEDUCTION_RATE_MULTI_2 = 0.10

    PAY_PERIOD_MULTIPLIER = {
        PayPeriodFields.WEEKLY: 30,
        PayPeriodFields.BI_WEEKLY: 60,
        PayPeriodFields.SEMI_MONTHLY: 65,
        PayPeriodFields.MONTHLY: 130,
    }

    def _calculate_disposable_earnings(self, record):
        """
        Calculates disposable earnings by subtracting mandatory deductions from gross pay.
        """
        state = gc.StateAbbreviations(record.get(
            EmployeeFields.WORK_STATE)).get_state_name_and_abbr()
        de = ChildSupport(state).calculate_de(record)
        return de

    def _get_fmw(self, pay_period):
        """
        Returns the Federal Minimum Wage threshold for the given pay period.
        """
        if not pay_period:
            raise ValueError("Pay period is missing in the record.")
        multiplier = self.PAY_PERIOD_MULTIPLIER.get(pay_period.lower())
        if not multiplier:
            raise ValueError(f"Invalid pay period: {pay_period}")
        return self.FMW_RATE * multiplier

    def get_single_student_amount(self, record):
        """
        Calculates the garnishment amount for a single student loan.
        """
        try:
            de = self._calculate_disposable_earnings(record)
            fmw = self._get_fmw(record.get(EmployeeFields.PAY_PERIOD))

            if de <= fmw:
                return {
                    "student_loan_amt": "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to the exempt amount."
                }

            deduction = min(
                de * self.DEDUCTION_RATE_SINGLE_1,
                de * self.DEDUCTION_RATE_SINGLE_2,
                de - fmw
            )
            return {
                "student_loan_amt": {"student_loan_amt1": round(deduction, 2)},
                "disposable_earning": de
            }

        except Exception as e:
            return {
                "student_loan_amt": f"Error calculating single student loan amount: {e}"
            }

    def get_multiple_student_amount(self, record):
        """
        Calculates the garnishment amounts for multiple student loans.
        """
        try:
            de = self._calculate_disposable_earnings(record)
            fmw = self._get_fmw(record.get(EmployeeFields.PAY_PERIOD))

            if de <= fmw:
                msg = "Student loan withholding cannot be applied because Disposable Earnings are less than or equal to the exempt amount."
                return {"student_loan_amt1": msg, "student_loan_amt2": msg}

            return {
                "student_loan_amt": {
                    "student_loan_amt1": round(de * self.DEDUCTION_RATE_MULTI_1, 2),
                    "student_loan_amt2": round(de * self.DEDUCTION_RATE_MULTI_2, 2)
                },
                "disposable_earning": de
            }

        except Exception as e:
            return {
                "student_loan_amt": {
                    "student_loan_amt1": f"Error calculating multiple student loan amount: {e}",
                    "student_loan_amt2": f"Error calculating multiple student loan amount: {e}"
                },
                "disposable_earning": de
            }


class StudentLoanCalculator:
    """
    Service to calculate student loan garnishment for single or multiple cases.
    """

    def calculate(self, record):
        """
        Determines and calculates the appropriate student loan garnishment amount(s).
        Returns a DRF Response object on error.
        """
        try:
            count = record.get(EmployeeFields.NO_OF_STUDENT_DEFAULT_LOAN)
            student_loan = StudentLoan()

            if count == 1:
                return student_loan.get_single_student_amount(record)
            elif count and count > 1:
                return student_loan.get_multiple_student_amount(record)
            else:
                return {"student_loan_amt": 0, "de": 0}

        except Exception as e:
            return Response(
                {
                    "error": str(e),
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
