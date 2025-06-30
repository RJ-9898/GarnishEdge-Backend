import logging
from GarnishEdge_Project.garnishment_library import child_support as cs
from GarnishEdge_Project.garnishment_library import gar_resused_classes as gc
from GarnishEdge_Project.garnishment_library.utility_class import CalculationResponse as CR, ResponseHelper
from GarnishEdge_Project.garnishment_library.student_loan import StudentLoanCalculator
from GarnishEdge_Project.garnishment_library.federal_case import FederalTax
from GarnishEdge_Project.garnishment_library.state_tax import StateTaxLevyCalculator
from GarnishEdge_Project.garnishment_library.creditor_debt import CreditorDebtCalculator
from User_app.constants import (
    StateList as ST,
    EmployeeFields,
    CalculationMessages as CM,
    GarnishmentTypeFields as GT,
    ExemptConfigFields as EC,
    CommonConstants as CC,
    CalculationResponseFields as CF
)
from User_app.models import PriorityOrder
from User_app.serializers import PriorityOrderSerializer

logger = logging.getLogger(__name__)


class MultipleGarnishmentPriorityOrder:

    def get_priority_class(self, priority, record):
        try:
            priority_class_map = {
                GT.CHILD_SUPPORT: lambda: cs.ChildSupport(record.get(EmployeeFields.WORK_STATE)).calculate(record),
                GT.FEDERAL_TAX_LEVY: lambda: FederalTax().calculate(record),
                GT.STUDENT_DEFAULT_LOAN: lambda: StudentLoanCalculator().calculate(record),
                GT.STATE_TAX_LEVY: lambda: StateTaxLevyCalculator().calculate(record),
                GT.CREDITOR_DEBT: lambda: CreditorDebtCalculator().calculate(record),
            }
            return priority_class_map.get(priority)
        except Exception as e:
            logger.error(f"Error getting priority class for {priority}: {e}")
            return None

    def get_priority_order(self, state):
        try:
            queryset = PriorityOrder.objects.filter(state__iexact=state)
            if not queryset.exists():
                logger.warning(f"No priority order defined for state: {state}")
                return []
            return PriorityOrderSerializer(queryset, many=True).data
        except Exception as e:
            logger.error(
                f"Error fetching priority order for state {state}: {e}")
            return []

    def apply_garnishment_by_priority(self, record):
        try:
            state_info = gc.StateAbbreviations(
                record.get(EmployeeFields.WORK_STATE))
            state = state_info.get_state_name_and_abbr()

            # Calculate initial disposable earning (DE)
            disposable_income = cs.ChildSupport(state).calculate_de(record)

            priorities = self.get_priority_order(state)
            if not priorities:
                raise ValueError(f"No priorities defined for state: {state}")

            breakdown = {}

            for priority_data in priorities:
                priority = priority_data.get("garnishment_type")
                if disposable_income <= 0:
                    logger.info(
                        f"No disposable income left after priority {priority}")
                    break

                garnishment_func = self.get_priority_class(priority, record)
                if not garnishment_func:
                    logger.warning(
                        f"No handler defined for priority: {priority}")
                    continue

                try:
                    deduction = garnishment_func()
                    deduction_amount = min(deduction, disposable_income)
                    disposable_income -= deduction_amount
                    breakdown[priority] = deduction_amount
                except Exception as e:
                    logger.error(
                        f"Error applying garnishment for priority {priority}: {e}")
                    continue

            return breakdown, disposable_income

        except Exception as e:
            logger.exception("Failed to apply garnishment by priority")
            raise
