# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class UserAppApierrorlog(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField()
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    request_body = models.TextField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    error_message = models.TextField()
    traceback_info = models.TextField()

    class Meta:
        managed = False
        db_table = 'User_app_apierrorlog'


class UserAppApilog(models.Model):
    id = models.BigAutoField(primary_key=True)
    api_name = models.CharField(max_length=255)
    request_method = models.CharField(max_length=10)
    request_url = models.TextField()
    request_headers = models.TextField(blank=True, null=True)
    request_body = models.TextField(blank=True, null=True)
    status_code = models.IntegerField()
    error_message = models.TextField()
    traceback = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField()
    user = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'User_app_apilog'


class UserAppLogdata(models.Model):
    id = models.BigAutoField(primary_key=True)
    api_name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    endpoint = models.CharField(max_length=255)
    status_code = models.IntegerField()
    message = models.TextField()
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'User_app_logdata'


class UserAppLogentry(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.CharField(max_length=20)
    message = models.TextField()
    action = models.CharField(max_length=255, blank=True, null=True)
    details = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField()
    logger_name = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    line_number = models.IntegerField(blank=True, null=True)
    function_name = models.CharField(max_length=255, blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'User_app_logentry'


class ApiCallLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'api_call_log'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField('EmployerProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'authtoken_token'


class CreditorDebtAppliedRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    ee_id = models.CharField(max_length=255, blank=True, null=True)
    case_id = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    pay_period = models.CharField(max_length=255)
    withholding_cap = models.CharField(max_length=25005, blank=True, null=True)
    withholding_basis = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'creditor_debt_applied_rule'


class CreditorDebtExemptAmtConfig(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=50)
    pay_period = models.CharField(max_length=50)
    minimum_hourly_wage_basis = models.CharField(max_length=20, blank=True, null=True)
    minimum_wage_amount = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    multiplier_lt = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    condition_expression_lt = models.CharField(max_length=100, blank=True, null=True)
    lower_threshold_amount = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    lower_threshold_percent1 = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    lower_threshold_percent2 = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    multiplier_mid = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    condition_expression_mid = models.CharField(max_length=100, blank=True, null=True)
    mid_threshold_amount = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    mid_threshold_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    multiplier_ut = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    condition_expression_ut = models.CharField(max_length=100, blank=True, null=True)
    upper_threshold_amount = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    upper_threshold_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    de_range_lower_to_upper_threshold_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    de_range_lower_to_mid_threshold_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    de_range_mid_to_upper_threshold_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    deducted_basis_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    is_filing_status = models.CharField(max_length=100, blank=True, null=True)
    filing_status_percent = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    exempt_amt = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    rule = models.ForeignKey('CreditorDebtRule', models.DO_NOTHING)
    edit_permission = models.ForeignKey('CreditorDebtRuleEditPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'creditor_debt_exempt_amt_config'


class CreditorDebtRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(unique=True, max_length=255)
    rule = models.CharField(max_length=2500, blank=True, null=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'creditor_debt_rule'


class CreditorDebtRuleEditPermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)
    state_config = models.OneToOneField(CreditorDebtRule, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'creditor_debt_rule_edit_permission'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('EmployerProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoRestPasswordresetResetpasswordtoken(models.Model):
    created_at = models.DateTimeField()
    key = models.CharField(unique=True, max_length=64)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=512)
    user = models.ForeignKey('EmployerProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_rest_passwordreset_resetpasswordtoken'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class EmployeeBatchData(models.Model):
    id = models.BigAutoField(primary_key=True)
    ee_id = models.CharField(unique=True, max_length=255)
    case_id = models.CharField(unique=True, max_length=255)
    work_state = models.CharField(max_length=255)
    no_of_exemption_including_self = models.FloatField(blank=True, null=True)
    pay_period = models.CharField(max_length=255, blank=True, null=True)
    filing_status = models.CharField(max_length=255, blank=True, null=True)
    age = models.FloatField(blank=True, null=True)
    is_blind = models.BooleanField(blank=True, null=True)
    is_spouse_blind = models.BooleanField(blank=True, null=True)
    spouse_age = models.FloatField(blank=True, null=True)
    support_second_family = models.CharField(max_length=255)
    no_of_student_default_loan = models.FloatField(blank=True, null=True)
    arrears_greater_than_12_weeks = models.CharField(max_length=255)
    no_of_dependent_exemption = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employee_batch_data'


class EmployeeDetail(models.Model):
    id = models.BigAutoField(primary_key=True)
    ee_id = models.CharField(max_length=255)
    case_id = models.CharField(max_length=255)
    age = models.CharField(max_length=255)
    social_security_number = models.CharField(max_length=255)
    is_blind = models.BooleanField(blank=True, null=True)
    home_state = models.CharField(max_length=255)
    work_state = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, blank=True, null=True)
    number_of_exemptions = models.IntegerField()
    filing_status = models.CharField(max_length=255)
    marital_status = models.CharField(max_length=255)
    number_of_student_default_loan = models.IntegerField()
    support_second_family = models.BooleanField()
    spouse_age = models.IntegerField(blank=True, null=True)
    is_spouse_blind = models.BooleanField(blank=True, null=True)
    record_import = models.DateTimeField()
    record_updated = models.DateTimeField()
    garnishment_fees_status = models.BooleanField()
    garnishment_fees_suspended_till = models.DateField()
    pay_period = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'employee_detail'


class EmployerProfile(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    email = models.CharField(unique=True, max_length=254)
    username = models.CharField(unique=True, max_length=100)
    employer_name = models.CharField(max_length=100)
    federal_employer_identification_number = models.CharField(max_length=255, blank=True, null=True)
    street_name = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    number_of_employees = models.IntegerField(blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField()
    is_staff = models.BooleanField()
    is_superuser = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'employer_profile'


class EmployerProfileGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    employer_profile = models.ForeignKey(EmployerProfile, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'employer_profile_groups'
        unique_together = (('employer_profile', 'group'),)


class EmployerProfileUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    employer_profile = models.ForeignKey(EmployerProfile, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'employer_profile_user_permissions'
        unique_together = (('employer_profile', 'permission'),)


class GarnishmentBatchData(models.Model):
    id = models.BigAutoField(primary_key=True)
    ee_id = models.CharField(max_length=255)
    case_id = models.CharField(unique=True, max_length=255)
    garnishment_type = models.CharField(max_length=255)
    ordered_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    arrear_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    current_medical_support = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    past_due_medical_support = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    current_spousal_support = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    past_due_spousal_support = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employee_case = models.OneToOneField(EmployeeBatchData, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'garnishment_batch_data'


class GarnishmentFees(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    pay_period = models.CharField(max_length=255)
    amount = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255)
    rules = models.CharField(max_length=255)
    payable_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'garnishment_fees'
        unique_together = (('state', 'pay_period'),)


class GarnishmentFeesRules(models.Model):
    id = models.BigAutoField(primary_key=True)
    rule = models.CharField(max_length=255)
    maximum_fee_deduction = models.CharField(max_length=255)
    per_pay_period = models.DecimalField(max_digits=250, decimal_places=2)
    per_month = models.DecimalField(max_digits=250, decimal_places=2)
    per_remittance = models.DecimalField(max_digits=250, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'garnishment_fees_rules'


class GarnishmentFeesStatesRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=255)
    pay_period = models.CharField(max_length=255)
    rule = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'garnishment_fees_states_rule'


class GarnishmentOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    eeid = models.CharField(max_length=254)
    fein = models.CharField(max_length=254)
    case_id = models.CharField(max_length=255, blank=True, null=True)
    work_state = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    sdu = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    amount = models.DecimalField(max_digits=250, decimal_places=2)
    arrear_greater_than_12_weeks = models.BooleanField()
    arrear_amount = models.DecimalField(max_digits=250, decimal_places=2)
    record_updated = models.DateTimeField()
    employee = models.ForeignKey(EmployeeDetail, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'garnishment_order'


class IwoDetailsPdf(models.Model):
    iwo_id = models.AutoField(db_column='IWO_ID', primary_key=True)  # Field name made lowercase.
    cid = models.CharField(max_length=250)
    ee_id = models.CharField(max_length=250)
    iwo_status = models.CharField(db_column='IWO_Status', max_length=250)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'iwo_details_pdf'


class IwoPdfFiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    pdf_url = models.CharField(max_length=200)
    uploaded_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'iwo_pdf_files'


class PayrollTaxesBatchData(models.Model):
    id = models.BigAutoField(primary_key=True)
    ee_id = models.CharField(unique=True, max_length=255)
    case_id = models.CharField(unique=True, max_length=255)
    wages = models.DecimalField(max_digits=10, decimal_places=2)
    commission_and_bonus = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    non_accountable_allowances = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    debt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    exemption_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    federal_income_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    social_security_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    medicare_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    state_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    local_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    union_dues = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    wilmington_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    medical_insurance_pretax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    industrial_insurance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    life_insurance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    california_sdi = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    employee_case = models.OneToOneField(EmployeeBatchData, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'payroll_taxes_batch_data'


class PeoTable(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    peo_id = models.AutoField(primary_key=True)
    peo_name = models.CharField(max_length=255)
    email = models.CharField(unique=True, max_length=254)
    password1 = models.CharField(max_length=255)
    password2 = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'peo_table'


class Setting(models.Model):
    id = models.BigAutoField(primary_key=True)
    employer_id = models.IntegerField()
    modes = models.BooleanField()
    visibilitys = models.BooleanField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'setting'


class StateTaxLevyAppliedRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    ee_id = models.CharField(max_length=1000, blank=True, null=True)
    case_id = models.CharField(max_length=1000, blank=True, null=True)
    state = models.CharField(max_length=1000, blank=True, null=True)
    pay_period = models.CharField(max_length=1000)
    deduction_basis = models.CharField(max_length=1000, blank=True, null=True)
    withholding_cap = models.CharField(max_length=1000, blank=True, null=True)
    withholding_limit = models.CharField(max_length=1000, blank=True, null=True)
    withholding_basis = models.CharField(max_length=1000, blank=True, null=True)
    withholding_limit_rule = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'state_tax_levy_applied_rule'


class StateTaxLevyExemptAmtConfig(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=255)
    pay_period = models.CharField(max_length=255)
    minimum_hourly_wage_basis = models.CharField(max_length=255)
    minimum_wage_amount = models.DecimalField(max_digits=250, decimal_places=4)
    multiplier_lt = models.DecimalField(max_digits=250, decimal_places=4)
    condition_expression_lt = models.CharField(blank=True, null=True)
    lower_threshold_amount = models.DecimalField(max_digits=250, decimal_places=4)
    multiplier_ut = models.DecimalField(max_digits=250, decimal_places=4)
    condition_expression_ut = models.CharField(blank=True, null=True)
    upper_threshold_amount = models.DecimalField(max_digits=250, decimal_places=4)
    state_config = models.ForeignKey('StateTaxLevyRule', models.DO_NOTHING)
    edit_permission = models.ForeignKey('StateTaxLevyRuleEditPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'state_tax_levy_exempt_amt_config'


class StateTaxLevyRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(unique=True, max_length=255)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit_rule = models.CharField(max_length=455, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'state_tax_levy_rule'


class StateTaxLevyRuleEditPermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)
    state_config = models.OneToOneField(StateTaxLevyRule, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'state_tax_levy_rule_edit_permission'


class TokenBlacklistBlacklistedtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    blacklisted_at = models.DateTimeField()
    token = models.OneToOneField('TokenBlacklistOutstandingtoken', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'token_blacklist_blacklistedtoken'


class TokenBlacklistOutstandingtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    user = models.ForeignKey(EmployerProfile, models.DO_NOTHING, blank=True, null=True)
    jti = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'token_blacklist_outstandingtoken'


class WithholdingOrderData(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.CharField(max_length=250)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    case_id = models.CharField(max_length=255)
    order_id = models.CharField(max_length=255)
    remittance_id = models.CharField(max_length=255)
    fein = models.CharField(max_length=255)
    employee_name = models.CharField(max_length=255)
    child1_name = models.CharField(max_length=255, blank=True, null=True)
    child2_name = models.CharField(max_length=255, blank=True, null=True)
    child3_name = models.CharField(max_length=255, blank=True, null=True)
    child4_name = models.CharField(max_length=255, blank=True, null=True)
    child5_name = models.CharField(max_length=255, blank=True, null=True)
    child6_name = models.CharField(max_length=255, blank=True, null=True)
    child1_dob = models.CharField(max_length=255, blank=True, null=True)
    child2_dob = models.CharField(max_length=255, blank=True, null=True)
    child3_dob = models.CharField(max_length=255, blank=True, null=True)
    child4_dob = models.CharField(max_length=255, blank=True, null=True)
    child5_dob = models.CharField(max_length=255, blank=True, null=True)
    child6_dob = models.CharField(max_length=255, blank=True, null=True)
    past_due_cash_medical_support_payperiod = models.CharField(max_length=255, blank=True, null=True)
    current_spousal_support_payperiod = models.CharField(max_length=255, blank=True, null=True)
    past_due_spousal_support_payperiod = models.CharField(max_length=255, blank=True, null=True)
    other_order_payperiod = models.CharField(max_length=255, blank=True, null=True)
    total_amount_to_withhold_payperiod = models.CharField(max_length=255, blank=True, null=True)
    current_child_support_payperiod = models.CharField(max_length=255, blank=True, null=True)
    past_due_child_support_payperiod = models.CharField(max_length=255, blank=True, null=True)
    current_cash_medical_support_payperiod = models.CharField(max_length=255, blank=True, null=True)
    current_child_support_amt = models.FloatField(blank=True, null=True)
    past_due_cash_medical_support = models.FloatField(blank=True, null=True)
    total_amt_to_withhold = models.FloatField(blank=True, null=True)
    lump_sum_payment_amt = models.FloatField(blank=True, null=True)
    disposable_income_percentage = models.CharField(max_length=255, blank=True, null=True)
    current_spousal_support = models.FloatField(blank=True, null=True)
    other_order_amount = models.FloatField(blank=True, null=True)
    ordered_amount_per_weekly = models.FloatField(blank=True, null=True)
    ordered_amount_per_biweekly = models.FloatField(blank=True, null=True)
    ordered_amount_per_monthly = models.FloatField(blank=True, null=True)
    ordered_amount_per_semimonthly = models.FloatField(blank=True, null=True)
    final_payment_amount = models.FloatField(blank=True, null=True)
    past_due_child_support = models.FloatField(blank=True, null=True)
    past_due_spousal_support = models.FloatField(blank=True, null=True)
    current_cash_medical_support = models.FloatField(blank=True, null=True)
    termination_date = models.CharField(max_length=255, blank=True, null=True)
    tribal_payee = models.CharField(max_length=255, blank=True, null=True)
    income_withholding_order = models.CharField(max_length=255, blank=True, null=True)
    arrears_greater_than_12_weeks = models.CharField(max_length=255, blank=True, null=True)
    one_time_order = models.CharField(max_length=255, blank=True, null=True)
    termination_of_iwo = models.CharField(max_length=255, blank=True, null=True)
    amended_iwo = models.CharField(max_length=255, blank=True, null=True)
    never_employed_no_income = models.CharField(max_length=255, blank=True, null=True)
    not_currently_employed = models.CharField(max_length=255, blank=True, null=True)
    child_support_agency = models.CharField(max_length=255, blank=True, null=True)
    court = models.CharField(max_length=255, blank=True, null=True)
    attorney = models.CharField(max_length=255, blank=True, null=True)
    private_individual = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'withholding_order_data'
