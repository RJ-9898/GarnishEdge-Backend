# models.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class EmployerProfileManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Employer_Profile(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    employer_name = models.CharField(max_length=100, default="ABS")
    federal_employer_identification_number = models.CharField(
        max_length=255, null=True, blank=True)
    street_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=10, null=True, blank=True)
    number_of_employees = models.IntegerField(null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    # Required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = EmployerProfileManager()

    class Meta:
        db_table = "employer_profile"

    def __str__(self):
        return self.email


class peo_table(AbstractBaseUser):
    peo_id = models.AutoField(primary_key=True)
    peo_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password1 = models.CharField(max_length=255)
    password2 = models.CharField(max_length=255)

    class Meta:
        db_table = "peo_table"


class employee_detail(models.Model):
    ee_id = models.CharField(max_length=255)
    case_id = models.CharField(max_length=255)
    age = models.CharField(max_length=255)
    social_security_number = models.CharField(max_length=255)
    is_blind = models.BooleanField(null=True, blank=True)
    home_state = models.CharField(max_length=255)
    work_state = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, null=True, blank=True)
    number_of_exemptions = models.IntegerField()
    filing_status = models.CharField(max_length=255)
    marital_status = models.CharField(max_length=255)
    number_of_student_default_loan = models.IntegerField()
    support_second_family = models.BooleanField()
    spouse_age = models.IntegerField(null=True, blank=True)
    is_spouse_blind = models.BooleanField(null=True, blank=True)
    record_import = models.DateTimeField(auto_now_add=True)
    record_updated = models.DateTimeField(auto_now_add=True)
    garnishment_fees_status = models.BooleanField()
    garnishment_fees_suspended_till = models.DateField()
    pay_period = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['ee_id']),
            models.Index(fields=['case_id']),
            models.Index(fields=['ee_id', 'case_id']),
        ]
        db_table = "employee_detail"


class garnishment_order(models.Model):
    employee = models.ForeignKey(
        employee_detail, on_delete=models.CASCADE, related_name="garnishments")
    eeid = models.CharField(max_length=254)
    fein = models.CharField(max_length=254)
    case_id = models.CharField(max_length=255, null=True, blank=True)
    work_state = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    sdu = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(max_length=255, null=True, blank=True)
    end_date = models.DateField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=250, decimal_places=2)
    arrear_greater_than_12_weeks = models.BooleanField(
        default=False, blank=False)
    arrear_amount = models.DecimalField(max_digits=250, decimal_places=2)
    record_updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['eeid']),
            models.Index(fields=['case_id']),
            models.Index(fields=['case_id', 'eeid']),
        ]
        db_table = "garnishment_order"


class IWOPDFFiles(models.Model):
    name = models.CharField(max_length=255)
    pdf_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "iwo_pdf_files"


class IWO_Details_PDF(models.Model):
    IWO_ID = models.AutoField(primary_key=True)
    cid = models.CharField(max_length=250)
    ee_id = models.CharField(max_length=250)
    IWO_Status = models.CharField(max_length=250)

    class Meta:
        db_table = "iwo_details_pdf"


class LogEntry(models.Model):
    action = models.CharField(max_length=255)
    details = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.timestamp} - {self.user} - {self.action}'

    class Meta:
        db_table = "log_entry"


class setting(models.Model):
    employer_id = models.IntegerField()
    modes = models.BooleanField()
    visibilitys = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "setting"


class APICallLog(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.path} - {self.method} - {self.timestamp}'

    class Meta:
        db_table = "api_call_log"


class garnishment_fees_states_rule(models.Model):
    state = models.CharField(max_length=255)
    pay_period = models.CharField(max_length=255)
    rule = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['state'])
        ]
        db_table = "garnishment_fees_states_rule"


class garnishment_fees_rules(models.Model):
    rule = models.CharField(max_length=255)
    maximum_fee_deduction = models.CharField(max_length=255)
    per_pay_period = models.DecimalField(max_digits=250, decimal_places=2)
    per_month = models.DecimalField(max_digits=250, decimal_places=2)
    per_remittance = models.DecimalField(max_digits=250, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['rule'])
        ]
        db_table = "garnishment_fees_rules"


class garnishment_fees(models.Model):
    state = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    pay_period = models.CharField(max_length=255)
    amount = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255)
    rules = models.CharField(max_length=255)
    payable_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['type']),
            models.Index(fields=['pay_period', 'state']),
        ]
        db_table = "garnishment_fees"
        unique_together = ('state', 'pay_period')


class employee_batch_data(models.Model):
    ee_id = models.CharField(max_length=255, unique=True)
    case_id = models.CharField(max_length=255, unique=True)
    work_state = models.CharField(max_length=255)
    no_of_exemption_including_self = models.FloatField(null=True, blank=True)
    pay_period = models.CharField(max_length=255, null=True, blank=True)
    filing_status = models.CharField(max_length=255, null=True, blank=True)
    age = models.FloatField(null=True, blank=True)
    is_blind = models.BooleanField(null=True, blank=True)
    is_spouse_blind = models.BooleanField(null=True, blank=True)
    spouse_age = models.FloatField(null=True, blank=True)
    support_second_family = models.CharField(max_length=255)
    no_of_student_default_loan = models.FloatField(null=True, blank=True)
    arrears_greater_than_12_weeks = models.CharField(max_length=255)
    no_of_dependent_exemption = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['ee_id', 'case_id']),
        ]

        db_table = "employee_batch_data"

    def __str__(self):
        return f"Employee {self.ee_id} - Case {self.case_id}"


class garnishment_batch_data(models.Model):
    employee_case = models.OneToOneField(
        employee_batch_data,
        to_field='case_id',
        on_delete=models.CASCADE,
        related_name='garnishment_data'
    )
    ee_id = models.CharField(max_length=255)
    case_id = models.CharField(max_length=255, unique=True)
    garnishment_type = models.CharField(max_length=255)
    ordered_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    arrear_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    current_medical_support = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    past_due_medical_support = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    current_spousal_support = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    past_due_spousal_support = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['ee_id']),
            models.Index(fields=['ee_id', 'case_id']),
        ]
        db_table = "garnishment_batch_data"


class payroll_taxes_batch_data(models.Model):
    employee_case = models.OneToOneField(
        employee_batch_data,
        to_field='case_id',
        on_delete=models.CASCADE,
        related_name='payroll_data'
    )
    ee_id = models.CharField(max_length=255, unique=True)
    case_id = models.CharField(max_length=255, unique=True)
    wages = models.DecimalField(max_digits=10, decimal_places=2)
    commission_and_bonus = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    non_accountable_allowances = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    gross_pay = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    debt = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    exemption_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    net_pay = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    federal_income_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    social_security_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    medicare_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    state_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    local_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    union_dues = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    wilmington_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    medical_insurance_pretax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    industrial_insurance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    life_insurance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    california_sdi = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['ee_id', 'case_id']),
        ]

        db_table = "payroll_taxes_batch_data"


# Model to store log details in the database
class LogEntry(models.Model):
    level = models.CharField(max_length=20)
    message = models.TextField()
    action = models.CharField(max_length=255, blank=True, null=True)
    details = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    logger_name = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    line_number = models.IntegerField(blank=True, null=True)
    function_name = models.CharField(max_length=255, blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.timestamp} - {self.level} - {self.message}"

    db_table = "log_entry"


class Logdata(models.Model):
    api_name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    endpoint = models.CharField(max_length=255)
    status_code = models.IntegerField()
    message = models.TextField()
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.api_name} - {self.status} - {self.status_code}"

    db_table = "log_data"


class withholding_order_data(models.Model):
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

    past_due_cash_medical_support_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    current_spousal_support_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    past_due_spousal_support_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    other_order_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    total_amount_to_withhold_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    current_child_support_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    past_due_child_support_payperiod = models.CharField(
        max_length=255, blank=True, null=True)
    current_cash_medical_support_payperiod = models.CharField(
        max_length=255, blank=True, null=True)

    current_child_support_amt = models.FloatField(blank=True, null=True)
    past_due_cash_medical_support = models.FloatField(blank=True, null=True)
    total_amt_to_withhold = models.FloatField(blank=True, null=True)
    lump_sum_payment_amt = models.FloatField(blank=True, null=True)
    disposable_income_percentage = models.CharField(
        max_length=255, blank=True, null=True)
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
    income_withholding_order = models.CharField(
        max_length=255, blank=True, null=True)
    arrears_greater_than_12_weeks = models.CharField(
        max_length=255, blank=True, null=True)
    one_time_order = models.CharField(max_length=255, blank=True, null=True)
    termination_of_iwo = models.CharField(
        max_length=255, blank=True, null=True)
    amended_iwo = models.CharField(max_length=255, blank=True, null=True)
    never_employed_no_income = models.CharField(
        max_length=255, blank=True, null=True)
    not_currently_employed = models.CharField(
        max_length=255, blank=True, null=True)
    child_support_agency = models.CharField(
        max_length=255, blank=True, null=True)
    court = models.CharField(max_length=255, blank=True, null=True)
    attorney = models.CharField(max_length=255, blank=True, null=True)
    private_individual = models.CharField(
        max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.employee_name} - {self.case_id}"

    class Meta:
        indexes = [
            models.Index(fields=['id'])
        ]
        db_table = "withholding_order_data"


class state_tax_levy_rule(models.Model):
    state = models.CharField(max_length=255, unique=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit_rule = models.CharField(
        max_length=455, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['state'])
        ]
        db_table = "state_tax_levy_rule"


class state_tax_levy_rule_edit_permission(models.Model):
    state_config = models.OneToOneField(  # One-to-One with creditor_debt_rule
        state_tax_levy_rule,
        on_delete=models.CASCADE,
        related_name="edit_permission"
    )
    state = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['state'])
        ]
        db_table = "state_tax_levy_rule_edit_permission"


class state_tax_levy_exempt_amt_config(models.Model):
    state_config = models.ForeignKey(
        state_tax_levy_rule,
        on_delete=models.CASCADE,
        related_name="state_tax_levy_exempt_amounts"
    )
    edit_permission = models.ForeignKey(
        state_tax_levy_rule_edit_permission,
        on_delete=models.CASCADE,
        related_name="exempt_amounts"
    )
    state = models.CharField(max_length=255,)
    pay_period = models.CharField(max_length=255)
    minimum_hourly_wage_basis = models.CharField(max_length=255)
    minimum_wage_amount = models.DecimalField(max_digits=250, decimal_places=4)
    multiplier_lt = models.DecimalField(max_digits=250, decimal_places=4)
    condition_expression_lt = models.CharField(null=True, blank=True)
    lower_threshold_amount = models.DecimalField(
        max_digits=250, decimal_places=4)
    multiplier_ut = models.DecimalField(max_digits=250, decimal_places=4)
    condition_expression_ut = models.CharField(null=True, blank=True)
    upper_threshold_amount = models.DecimalField(
        max_digits=250, decimal_places=4)

    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['pay_period', 'state']),
        ]
        db_table = "state_tax_levy_exempt_amt_config"


class state_tax_levy_applied_rule(models.Model):
    ee_id = models.CharField(max_length=1000, blank=True, null=True)
    case_id = models.CharField(max_length=1000, blank=True, null=True)
    state = models.CharField(max_length=1000, blank=True, null=True)
    pay_period = models.CharField(max_length=1000)
    deduction_basis = models.CharField(max_length=1000, blank=True, null=True)
    withholding_cap = models.CharField(max_length=1000, blank=True, null=True)
    withholding_limit = models.CharField(
        max_length=1000, blank=True, null=True)
    withholding_basis = models.CharField(
        max_length=1000, blank=True, null=True)
    withholding_limit_rule = models.CharField(
        max_length=1000, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['ee_id'])
        ]
        db_table = "state_tax_levy_applied_rule"


class creditor_debt_rule(models.Model):
    state = models.CharField(max_length=255, unique=True)
    rule = models.CharField(max_length=2500, blank=True, null=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['state'])
        ]
        db_table = "creditor_debt_rule"


class creditor_debt_rule_edit_permission(models.Model):
    state_config = models.OneToOneField(  # One-to-One with creditor_debt_rule
        creditor_debt_rule,
        on_delete=models.CASCADE,
        related_name="edit_permission"
    )
    state = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    deduction_basis = models.CharField(max_length=255, blank=True, null=True)
    withholding_limit = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['state'])
        ]
        db_table = "creditor_debt_rule_edit_permission"


class creditor_debt_exempt_amt_config(models.Model):
    rule = models.ForeignKey(
        creditor_debt_rule,
        on_delete=models.CASCADE,
        related_name="exempt_amounts"
    )
    edit_permission = models.ForeignKey(
        creditor_debt_rule_edit_permission,
        on_delete=models.CASCADE,
        related_name="exempt_amounts"
    )
    state = models.CharField(max_length=50)
    pay_period = models.CharField(max_length=50)
    minimum_hourly_wage_basis = models.CharField(
        max_length=20, null=True, blank=True)
    minimum_wage_amount = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    multiplier_lt = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    condition_expression_lt = models.CharField(
        max_length=100, null=True, blank=True)
    lower_threshold_amount = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    lower_threshold_percent1 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    lower_threshold_percent2 = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    multiplier_mid = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    condition_expression_mid = models.CharField(
        max_length=100, null=True, blank=True)
    mid_threshold_amount = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    mid_threshold_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    multiplier_ut = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    condition_expression_ut = models.CharField(
        max_length=100, null=True, blank=True)
    upper_threshold_amount = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    upper_threshold_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    de_range_lower_to_upper_threshold_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    de_range_lower_to_mid_threshold_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    de_range_mid_to_upper_threshold_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    deducted_basis_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    is_filing_status = models.CharField(max_length=100, null=True, blank=True)
    filing_status_percent = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    exempt_amt = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['pay_period', 'state']),
        ]
        db_table = "creditor_debt_exempt_amt_config"


class creditor_debt_applied_rule(models.Model):

    ee_id = models.CharField(max_length=255, blank=True, null=True)
    case_id = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    pay_period = models.CharField(max_length=255)
    withholding_cap = models.CharField(max_length=25005, blank=True, null=True)
    withholding_basis = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['pay_period', 'state']),
        ]
        db_table = "creditor_debt_applied_rule"


class APILog(models.Model):
    api_name = models.CharField(max_length=255)
    request_method = models.CharField(max_length=10)
    request_url = models.TextField()
    request_headers = models.TextField(null=True, blank=True)
    request_body = models.TextField(null=True, blank=True)
    status_code = models.IntegerField()
    error_message = models.TextField()
    traceback = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.api_name} ({self.status_code})"

    db_table = "api_log"


class ApiErrorLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    request_body = models.TextField(null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    error_message = models.TextField()
    traceback_info = models.TextField()

    def __str__(self):
        return f"{self.request_method} {self.request_path} - {self.error_message[:50]}"
