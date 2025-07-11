class CalculationFields:
    GROSS_PAY = 'gross_pay'
    NET_PAY = 'net_pay'
    WAGES = 'wages'
    COMMISSION_AND_BONUS = 'commission_and_bonus'
    NON_ACCOUNTABLE_ALLOWANCES = 'non_accountable_allowances'
    GARNISHMENT_DATA = 'garnishment_data'
    MEDICAL_INSURANCE = 'medical_insurance'
    ORDERED_AMOUNT = 'ordered_amount'
    ARREAR_AMOUNT = 'arrear_amount'
    GARNISHMENT_TYPE = "garnishment_type"
    CURRENT_MEDICAL_SUPPORT = 'current_medical_support'
    PAST_DUE_MEDICAL_SUPPORT = 'past_due_medical_support'
    CURRENT_SPOUSAL_SUPPORT = 'current_spousal_support'
    PAST_DUE_SPOUSAL_SUPPORT = 'past_due_spousal_support'


class GarnishmentTypeFields:
    CHILD_SUPPORT = 'child support'
    FEDERAL_TAX_LEVY = 'federal tax levy'
    STUDENT_DEFAULT_LOAN = 'student default loan'
    STATE_TAX_LEVY = 'state tax levy'
    CREDITOR_DEBT = 'creditor debt'


class GarnishmentTypeResponse:
    STUDENT_DEFAULT_LOAN = "student_default_loan"
    FEDERAL_TAX_LEVY = 'federal_tax_levy'


class PayPeriodFields:
    WEEKLY = 'weekly'
    BI_WEEKLY = 'biweekly'
    SEMI_MONTHLY = 'semimonthly'
    MONTHLY = 'monthly'


class FilingStatusFields:
    SINGLE = 'single'
    MARRIED_FILING_JOINT_RETURN = 'married_filing_joint_return'
    MARRIED_FILING_SEPARATE_RETURN = 'married_filing_separate_return'
    HEAD_OF_HOUSEHOLD = 'head_of_household'
    QUALIFYING_WIDOWERS = 'qualifying_widowers'
    ADDITIONAL_EXEMPT_AMOUNT = 'additional_exempt_amount'


class PayrollTaxesFields:
    FEDERAL_INCOME_TAX = 'federal_income_tax'
    SOCIAL_SECURITY_TAX = 'social_security_tax'
    MEDICARE_TAX = 'medicare_tax'
    STATE_TAX = 'state_tax'
    LOCAL_TAX = 'local_tax'
    UNION_DUES = 'union_dues'
    MEDICAL_INSURANCE_PRETAX = 'medical_insurance_pretax'
    LIFE_INSURANCE = 'life_insurance'
    INDUSTRIAL_INSURANCE = 'industrial_insurance'
    CALIFORNIA_SDI = 'california_sdi'
    PAYROLL_TAXES = 'payroll_taxes'
    WILMINGTON_TAX = "wilmington_tax"
    FAMLI_TAX = 'famli_tax'


class EmployeeFields:
    EMPLOYEE_ID = 'ee_id'
    STATE = 'state'
    CASE_ID = 'case_id'
    WORK_STATE = 'work_state'
    HOME_STATE = 'home_state'
    BLIND = 'blind'
    SPOUSE_AGE = 'spouse_age'
    PAY_PERIOD = 'pay_period'
    DEBT_TYPE = "debt_type"
    GARN_START_DATE = 'garn_start_date'
    STATEMENT_OF_EXEMPTION_RECEIVED_DATE = 'statement_of_exemption_received_date'
    IS_CONSUMER_DEBT = 'is_consumer_debt'
    CONSUMER_DEBT = 'consumer_debt'
    NON_CONSUMER_DEBT = 'non_consumer_debt'
    PAYROLL_DATE = 'payroll_date'
    FILING_STATUS = 'filing_status'
    GROSS_PAY = 'gross_pay'
    GENDER = 'gender'
    NET_PAY = 'net_pay'
    AGE = 'age'
    IS_BLIND = 'is_blind'
    SSN = 'social_security_number'
    IS_SPOUSE_BLIND = 'is_spouse_blind'
    SUPPORT_SECOND_FAMILY = 'support_second_family'
    NO_OF_STUDENT_DEFAULT_LOAN = 'no_of_student_default_loan'
    NO_OF_EXEMPTION_INCLUDING_SELF = 'no_of_exemption_including_self'
    ARREARS_GREATER_THAN_12_WEEKS = 'arrears_greater_than_12_weeks'
    GARNISHMENT_TYPE = "type"
    DEBT = "debt"
    EXEMPTION_AMOUNT = "exemption_amount"
    DIST_CODE = "dist_code"
    NO_OF_DEPENDENT_EXEMPTION = "no_of_dependent_exemption"
    NO_OF_DEPENDENT_CHILD = "no_of_dependent_child"
    IS_CASE_OF_NON_TAX_LEVY = "is_case_of_non_tax_levy"
    IS_CASE_OF_INCOME_TAX_LEVY = "is_case_of_income_tax_levy"
    GARNISHMENT_DATA = "garnishment_data"
    GARNISHMENT_FEES_STATUS = 'garnishment_fees_status'
    MARITAL_STATUS = 'marital_status'
    GARNISHMENT_FEES_SUSPENDED_TILL = 'garnishment_fees_suspended_till'


class ChildSupportFields:
    PRORATE = "prorate"
    DEVIDEEQUALLY = "divide equally"


class PriorityOrderFields:
    CURRENT_SUPPORT = "current_support"
    ARREARS = "arrears"
    SPOUSAL_SUPPORT = "spousal_support"
    MEDICAL_PREMIUMS = "medical_premiums"
    INSURANCE_PREMIUMS = "insurance_premiums"
    COURT_FEE = "court_fee"
    HEALTH_INSURANCE_PREMIUMS = "health_insurance_premiums"
    HEALTH_CARE_PREMIUMS = "health_care_premiums"
    MEDICAL_SUPPORT_COVERAGE = "medical_support_coverage"
    COURT_ORDERED_HEALTH_INSURANCE_PREMIUMS = "court_ordered_health_insurance_premiums"
    CURRENT_SPOUSAL_SUPPORT = "current_spousal_support"
    ARREARS_FOR_CHILD_SUPPORT = "arrears_for_child_support"
    ARREARS_FOR_SPOUSAL_SUPPORT = "arrears_for_spousal_support"
    CURRENT_CHILD_SUPPORT = "current_child_support"
    MEDICAL_SUPPORT_PREMIUM = "medical_support_premium"
    ARREARAGE = "arrearage"
    DELINQUENCY = "deliquency"
    CHILD_SUPPORT_ARREARS = "child_support_arrears"
    MEDICAL_SUPPORT = "medical_support"
    OTHER_SUPPORT = "other_support"
    CASH_MEDICAL_SUPPORT = "cash_medical_support"
    FULL_COST_OF_THE_PREMIUM = "full_cost_of_the_premium"
    CURRENT_CHILD_AND_SPOUSAL_SUPPORT = "current_child_&_spousal_support"
    MEDICAL_SUPPORT_PREMIUMS = "medical_support_premiums"
    OTHER_CHILD_SUPPORT_OBLIGATIONS = "other_child_support_obligations"
    MEDICAL_INSURANCE_PREMIUMS = "medical_insurance_premiums"
    FEES = "fees"
    REIMBURSEMENTS = "reimbursements"
    MEDICAL_SUPPORT_ARREARS = "medical_support_arrears"
    CASH_CHILD_SUPPORT = "cash_child_support"
    HEALTH_PREMIUMS = "health_premiums"
    CHILD_ARREARS = "child_arrears"
    SPOUSAL_ARREARS = "spousal_arrears"
    SURCHARGE = "surcharge"
    INTEREST = "interest"

    # List of all fields
    ALL_FIELDS = [
        CURRENT_SUPPORT, ARREARS, SPOUSAL_SUPPORT, MEDICAL_PREMIUMS, INSURANCE_PREMIUMS,
        COURT_FEE, HEALTH_INSURANCE_PREMIUMS, HEALTH_CARE_PREMIUMS, MEDICAL_SUPPORT_COVERAGE,
        COURT_ORDERED_HEALTH_INSURANCE_PREMIUMS, CURRENT_SPOUSAL_SUPPORT, ARREARS_FOR_CHILD_SUPPORT,
        ARREARS_FOR_SPOUSAL_SUPPORT, CURRENT_CHILD_SUPPORT, MEDICAL_SUPPORT_PREMIUM, ARREARAGE,
        DELINQUENCY, CHILD_SUPPORT_ARREARS, MEDICAL_SUPPORT, OTHER_SUPPORT, CASH_MEDICAL_SUPPORT,
        FULL_COST_OF_THE_PREMIUM, CURRENT_CHILD_AND_SPOUSAL_SUPPORT, MEDICAL_SUPPORT_PREMIUMS,
        OTHER_CHILD_SUPPORT_OBLIGATIONS, MEDICAL_INSURANCE_PREMIUMS, FEES, REIMBURSEMENTS,
        MEDICAL_SUPPORT_ARREARS, CASH_CHILD_SUPPORT, HEALTH_PREMIUMS, CHILD_ARREARS,
        SPOUSAL_ARREARS, SURCHARGE, INTEREST
    ]


class OtherFields:
    PAYROLL_DEDUCTIONS = "payroll_deductions"


class StateTaxLevyCalculationData:
    # Constants for calculation

    # threshould Values
    VALUE_LOWER = 30
    VALUE_UPPER = 40

    # fmw values
    FMW = 7.25

    # wages amount according to pay_period
    WEEKLY = 1
    BI_WEEKLY = 2
    SEMI_MONTHLY = 2.1667
    MONTHLY = 4.334


class ResponseMessages:
    SUCCESS = "Success"
    FAILURE = "Failure"
    INVALID_PAY_PERIOD = "Invalid pay period"
    INVALID_FILING_STATUS = "Invalid filing status"
    INVALID_WORK_STATE = "Invalid work state"
    INVALID_GARNISHMENT_TYPE = "Invalid garnishment type"
    INVALID_EMPLOYEE_ID = "Invalid employee ID"
    INVALID_CASE_ID = "Invalid case ID"
    INVALID_PAYROLL_TAXES = "Invalid payroll taxes data"
    INVALID_PAYROLL_DEDUCTIONS = "Invalid payroll deductions data"
    INVALID_GARNISHMENT_DATA = "Invalid garnishment data"


class BatchDetail:
    BATCH_ID = "batch_id"


class StateList:
    ALABAMA = "alabama"
    ALASKA = "alaska"
    ARIZONA = "arizona"
    ARKANSAS = "arkansas"
    CALIFORNIA = "california"
    COLORADO = "colorado"
    CONNECTICUT = "connecticut"
    DELAWARE = "delaware"
    FLORIDA = "florida"
    GEORGIA = "georgia"
    HAWAII = "hawaii"
    IDAHO = "idaho"
    ILLINOIS = "illinois"
    INDIANA = "indiana"
    IOWA = "iowa"
    KANSAS = "kansas"
    KENTUCKY = "kentucky"
    LOUISIANA = "louisiana"
    MAINE = "maine"
    MARYLAND = "maryland"
    MASSACHUSETTS = "massachusetts"
    MICHIGAN = "michigan"
    MINNESOTA = "minnesota"
    MISSISSIPPI = "mississippi"
    MISSOURI = "missouri"
    MONTANA = "montana"
    NEBRASKA = "nebraska"
    NEVADA = "nevada"
    NEW_HAMPSHIRE = "new hampshire"
    NEW_JERSEY = "new jersey"
    NEW_MEXICO = "new mexico"
    NEW_YORK = "new york"
    NORTH_CAROLINA = "north carolina"
    NORTH_DAKOTA = "north dakota"
    OHIO = "ohio"
    OKLAHOMA = "oklahoma"
    OREGON = "oregon"
    PENNSYLVANIA = "pennsylvania"
    RHODE_ISLAND = "rhode island"
    SOUTH_CAROLINA = "south carolina"
    SOUTH_DAKOTA = "south dakota"
    TENNESSEE = "tennessee"
    TEXAS = "texas"
    UTAH = "utah"
    VERMONT = "vermont"
    VIRGINIA = "virginia"
    WASHINGTON = "washington"
    WEST_VIRGINIA = "west virginia"
    WISCONSIN = "wisconsin"
    WYOMING = "wyoming"


class ExemptConfigFields:
    LOWER_THRESHOLD_AMOUNT = "lower_threshold_amount"
    MID_THRESHOLD_AMOUNT = "mid_threshold_amount"
    UPPER_THRESHOLD_AMOUNT = "upper_threshold_amount"
    LOWER_THRESHOLD_PERCENT1 = "lower_threshold_percent1"
    LOWER_THRESHOLD_PERCENT2 = "lower_threshold_percent2"
    UPPER_THRESHOLD_PERCENT = "upper_threshold_percent"
    EXEMPT_AMOUNT = "exempt_amt"
    FILING_STATUS_PERCENT = "filing_status_percent"
    DEDUCTED_BASIS_PERCENT = "deducted_basis_percent"
    DE_RANGE_LOWER_TO_MID_THRESHOLD_PERCENT = "de_range_lower_to_mid_threshold_percent"
    DE_RANGE_LOWER_TO_UPPER_THRESHOLD_PERCENT = "de_range_lower_to_upper_threshold_percent"
    DE_RANGE_MID_TO_UPPER_THRESHOLD_PERCENT = "de_range_mid_to_upper_threshold_percent"


class GarnishmentConstants:
    VALUE1 = 30
    VALUE2 = 40
    VALUE3 = 53.33

    DEFAULT_PERCENT = 0.25
    MASSACHUSETTS_PERCENT = 0.15
    ARIZONA_PERCENT = 0.10
    NEWYORK_PERCENT1 = 0.10
    NEWYORK_PERCENT2 = 0.25
    EXEMPT_AMOUNT = 25


class CalculationMessages:
    DE_LE_LOWER = "Disposable Earning <= Lower Threshold Amount"
    DE_GT_LOWER = "Disposable Earning > Lower Threshold Amount"
    DE_GT_LOWER_LT_UPPER = "Lower Threshold Amount <= Disposable Earning <= Upper Threshold Amount"
    DE_GT_UPPER = "Disposable Earning > Upper Threshold Amount"
    NO_OF_EXEMPTIONS_ONE = "Number of Exemption Including Self = 1"
    NO_OF_EXEMPTIONS_MORE = "Number of Exemption Including Self > 1"
    DISPOSABLE_EARNING = "Disposable Earning"
    GROSS_PAY = "Gross Pay"
    WITHHOLDING_AMT = "Withholding Amount"
    LOWER_THRESHOLD_AMOUNT = "Lower Threshold Amount"
    MID_THRESHOLD_AMOUNT = "Mid Threshold Amount"
    UPPER_THRESHOLD_AMOUNT = "Upper Threshold Amount"
    NA = "NA"


class JSONPath:
    DISPOSABLE_EARNING_RULES = 'configuration files/child support tables/disposable earning rules.json'
    MARRIED_FILING_JOINT_RETURN = 'configuration files/federal tables/married_filing_joint_return.json'
    ADDITIONAL_EXEMPT_AMOUNT = 'configuration files/federal tables/additional_exempt_amount.json'
    WITHHOLDING_RULES = 'configuration files/child support tables/withholding_rules.json'
    WITHHOLDING_LIMITS = 'configuration files/child support tables/withholding_limits.json'


class CalculationResponseFields:
    WITHHOLDING_AMT = "withholding_amt"
    WITHHOLDING_BASIS = "withholding_basis"
    DISPOSABLE_EARNING = "disposable_earning"
    WITHHOLDING_CAP = "withholding_cap"
    ER_DEDUCTION = "er_deduction"
    GARNISHMENT_FEES = "garnishment_fees"
    AGENCY = "agency"
    WITHHOLDING_LIMIT_RULE = "withholding_limit_rule"
    TOTAL_MANDATORY_DEDUCTION = "total_mandatory_deduction"
    GARNISHMENT_AMOUNT = "garnishment_amount"
    WITHHOLDING_ARREAR = "withholding_arrear"
    ALLOWABLE_DISPOSABLE_EARNING = "allowable_disposable_earning"
    ARREAR = "arrear"
    CREDITOR_DEBT = "creditor_debt"


class CommonConstants:
    WITHHOLDING_RULE_PLACEHOLDER = "Rule"
    NOT_FOUND = "Not Found"
    NOT_PERMITTED = "Not Permitted"


class RuleResponseMsg:
    DE_LEQ_LOWER_THRESHOLD = "de <= lower_threshold_amount"
    DE_GT_LOWER_AND_LT_UPPER_THRESHOLD = "de > lower_threshold_amount and de < upper_threshold_amount"
    DE_GT_UPPER_THRESHOLD = "de > upper_threshold_amount"
    DE_LT_UPPER_THRESHOLD = "de < upper_threshold_amount"
    DE_GT_LOWER_THRESHOLD = "de > lower_threshold_amount"
    DISPOSABLE_EARNING = "de"
    GROSS_PAY = "gp"


class AllocationMethods:
    PRORATE = "prorate"
    DEVIDEEQUALLY = "divide equally"
    CHILDSUPPORT = "child_support"
