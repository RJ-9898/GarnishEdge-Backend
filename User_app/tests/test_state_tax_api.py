import pytest
from User_app.models import state_tax_levy_exempt_amt_config
from User_app.serializers import CreditorDebtExemptAmtConfigSerializers
from GarnishEdge_Project.garnishment_library.state_tax import StateTaxLevyCalculator

import os
print("DJANGO_SETTINGS_MODULE =", os.getenv("DJANGO_SETTINGS_MODULE"))


@pytest.mark.django_db
def test_all_state_calculations_run_without_error():
    # Fetch and serialize config data
    queryset = state_tax_levy_exempt_amt_config.objects.all()
    serializer = CreditorDebtExemptAmtConfigSerializers(queryset, many=True)
    config_data = serializer.data

    # List of states to test
    state_list = [
        "new york", "arizona", "idaho", "georgia", "illinois", "maryland", "massachusetts", "indiana", "maine",
        "missouri", "new jersey", "north carolina", "pennsylvania", "vermont", "virginia", "arkansas", "delaware",
        "iowa", "kentucky", "oregon", "utah", "new mexico", "west virginia", "alabama", "hawaii", "wisconsin",
        "california", "minnesota", "montana", "colorado", "connecticut", "louisiana", "mississippi", "colorado"
    ]

    failed_states = []

    # Loop through all states and test calculation
    for state in state_list:
        record = {
            "ee_id": "EE005126",
            "work_state": state,
            "no_of_exemption_including_self": 1,
            "pay_period": "Weekly",
            "filing_status": "married_filing_separate",
            "wages": 708.84,
            "commission_and_bonus": 0,
            "non_accountable_allowances": 0,
            "gross_pay": 708.84,
            "payroll_taxes": {
                "federal_income_tax": 125.93,
                "social_security_tax": 0,
                "medicare_tax": 0,
                "state_tax": 0,
                "local_tax": 0,
                "union_dues": 0,
                "wilmington_tax": 0,
                "medical_insurance": 0,
                "industrial_insurance": 0,
                "life_insurance": 0,
                "california_sdi": 0,
                "famli_tax": 0
            },
            "net_pay": 906.83,
            "support_second_family": "No",
            "no_of_dependent_child": 0,
            "arrears_greater_than_12_weeks": "No",
            "garnishment_data": [
                {
                    "type": "State tax levy",
                    "data": [
                        {
                            "case_id": "C17685",
                            "ordered_amount": 0,
                            "arrear_amount": 0
                        }
                    ]
                }
            ]
        }

        try:
            result = StateTaxView().calculate(record, config_data)
            # If result is an unexpected type (like a raw HttpResponse), count it as failure
            if hasattr(result, 'status_code') and result.status_code != 200:
                failed_states.append(state)
        except Exception as e:
            print(f"Error for state {state}: {e}")
            failed_states.append(state)

    # Final assert: test should pass only if all states succeed
    assert not failed_states, f"State calculations failed for: {', '.join(failed_states)}"
