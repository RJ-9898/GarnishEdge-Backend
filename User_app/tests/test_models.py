import pytest
from django.utils import timezone
from User_app.models import Employer_Profile


@pytest.mark.django_db
def test_employer_profile_comprehensive():
    # Test creation with all fields
    employer = models.Employer_Profile.objects.create(
        email="comprehensive@example.com",
        username="comprehensive_user",
        employer_name="Comprehensive Employer",
        federal_employer_identification_number="12-3456789",
        street_name="123 Main St",
        city="Test City",
        state="Test State",
        country="Test Country",
        zipcode="12345",
        number_of_employees=100,
        department="IT",
        location="Headquarters"
    )

    # Test required fields
    assert employer.email == "comprehensive@example.com"
    assert employer.username == "comprehensive_user"
    assert employer.employer_name == "Comprehensive Employer"
    assert employer.is_active is True
    assert employer.is_staff is False
    assert employer.is_superuser is False

    # Test optional fields
    assert employer.federal_employer_identification_number == "12-3456789"
    assert employer.street_name == "123 Main St"
    assert employer.city == "Test City"
    assert employer.state == "Test State"
    assert employer.country == "Test Country"
    assert employer.zipcode == "12345"
    assert employer.number_of_employees == 100
    assert employer.department == "IT"
    assert employer.location == "Headquarters"

    # Test default values
    default_employer = models.Employer_Profile.objects.create(
        email="default@example.com",
        username="default_user"
    )
    assert default_employer.employer_name == "ABS"  # Default value
    assert default_employer.federal_employer_identification_number is None
    assert default_employer.street_name is None
    assert default_employer.city is None
    assert default_employer.state is None
    assert default_employer.country is None
    assert default_employer.zipcode is None
    assert default_employer.number_of_employees is None
    assert default_employer.department is None
    assert default_employer.location is None

    # Test unique constraints
    with pytest.raises(Exception):  # Should raise an exception for duplicate email
        models.Employer_Profile.objects.create(
            email="comprehensive@example.com",
            username="another_user"
        )

    with pytest.raises(Exception):  # Should raise an exception for duplicate username
        models.Employer_Profile.objects.create(
            email="another@example.com",
            username="comprehensive_user"
        )


@pytest.mark.django_db
def test_employer_profile_creation():
    employer = models.Employer_Profile.objects.create(
        email="test@example.com",
        username="testuser",
        employer_name="Test Employer"
    )
    assert employer.email == "test@example.com"
    assert employer.username == "testuser"
    assert employer.employer_name == "Test Employer"
    assert employer.is_active is True


#emplopyee_ profile test
@pytest.mark.django_db
def test_employee_detail_creation():
    emp = models.employee_detail.objects.create(
        ee_id="E123",
        age="30",
        social_security_number="123-45-6789",
        home_state="CA",
        work_state="CA",
        number_of_exemptions=1,
        filing_status="Single",
        marital_status="Single",
        number_of_student_default_loan=0,
        support_second_family=False,
        garnishment_fees_status=True,
        garnishment_fees_suspended_till="2024-12-31",
        case_id="C123",
        pay_period="Monthly"
    )
    assert emp.id is not None
    assert emp.ee_id == "E123"
    assert emp.home_state == "CA"

@pytest.mark.django_db
def test_employee_detail_required_fields():
    # Test creation with only required fields
    emp = models.employee_detail.objects.create(
        ee_id="E124",
        age="35",
        social_security_number="987-65-4321",
        home_state="NY",
        work_state="NY",
        number_of_exemptions=2,
        filing_status="Married",
        marital_status="Married",
        number_of_student_default_loan=1,
        support_second_family=True,
        garnishment_fees_status=False,
        garnishment_fees_suspended_till="2024-12-31",
        case_id="C124",
        pay_period="Biweekly"
    )
    
    # Test required fields
    assert emp.ee_id == "E124"
    assert emp.age == "35"
    assert emp.social_security_number == "987-65-4321"
    assert emp.home_state == "NY"
    assert emp.work_state == "NY"
    assert emp.number_of_exemptions == 2
    assert emp.filing_status == "Married"
    assert emp.marital_status == "Married"
    assert emp.number_of_student_default_loan == 1
    assert emp.support_second_family is True
    assert emp.garnishment_fees_status is False
    assert emp.case_id == "C124"
    assert emp.pay_period == "Biweekly"

@pytest.mark.django_db
def test_employee_detail_optional_fields():
    # Test creation with optional fields
    emp = models.employee_detail.objects.create(
        ee_id="E125",
        age="40",
        social_security_number="111-22-3333",
        home_state="TX",
        work_state="TX",
        number_of_exemptions=3,
        filing_status="Head of Household",
        marital_status="Divorced",
        number_of_student_default_loan=2,
        support_second_family=False,
        garnishment_fees_status=True,
        garnishment_fees_suspended_till="2024-12-31",
        case_id="C125",
        pay_period="Weekly",
        # Optional fields
        is_blind=True,
        gender="Male",
        spouse_age=38,
        is_spouse_blind=False
    )
    
    # Test optional fields
    assert emp.is_blind is True
    assert emp.gender == "Male"
    assert emp.spouse_age == 38
    assert emp.is_spouse_blind is False

@pytest.mark.django_db
def test_employee_detail_auto_fields():
    # Test auto-generated fields
    emp = models.employee_detail.objects.create(
        ee_id="E126",
        age="45",
        social_security_number="444-55-6666",
        home_state="FL",
        work_state="FL",
        number_of_exemptions=1,
        filing_status="Single",
        marital_status="Single",
        number_of_student_default_loan=0,
        support_second_family=False,
        garnishment_fees_status=True,
        garnishment_fees_suspended_till="2024-12-31",
        case_id="C126",
        pay_period="Monthly"
    )
    
    # Test auto-generated fields
    assert emp.record_import is not None
    assert emp.record_updated is not None
    assert isinstance(emp.record_import, timezone.datetime)
    assert isinstance(emp.record_updated, timezone.datetime)

@pytest.mark.django_db
def test_employee_detail_null_optional_fields():
    # Test creation with null optional fields
    emp = models.employee_detail.objects.create(
        ee_id="E127",
        age="50",
        social_security_number="777-88-9999",
        home_state="WA",
        work_state="WA",
        number_of_exemptions=1,
        filing_status="Single",
        marital_status="Single",
        number_of_student_default_loan=0,
        support_second_family=False,
        garnishment_fees_status=True,
        garnishment_fees_suspended_till="2024-12-31",
        case_id="C127",
        pay_period="Monthly"
    )
    
    # Test that optional fields are null
    assert emp.is_blind is None
    assert emp.gender is None
    assert emp.spouse_age is None
    assert emp.is_spouse_blind is None

#passed
@pytest.mark.django_db
def test_payroll_creation():
    payroll = models.payroll.objects.create(
        cid="C1",
        eeid="E1",
        payroll_date="2024-01-01",
        pay_date="2024-01-02",
        gross_pay=1000.00,
        net_pay=800.00,
        tax_federal_income_tax=100.00,
        tax_state_tax=50.00,
        tax_local_tax=10.00,
        tax_medicare_tax=20.00,
        tax_social_security="60.00",
        deduction_sdi=5.00,
        deduction_medical_insurance=15.00,
        deduction_401k=25.00,
        deduction_union_dues=10.00,
        deduction_voluntary=5.00,
        type="Regular",
        amount=800.00
    )
    assert payroll.gross_pay == 1000.00
    assert payroll.net_pay == 800.00
    assert payroll.cid == "C1"
    assert payroll.eeid == "E1"
    assert payroll.payroll_date == "2024-01-01"
    assert payroll.pay_date == "2024-01-02"
    assert payroll.type == "Regular"
    assert payroll.amount == 800.00
    assert payroll.tax_federal_income_tax == 100.00
    assert payroll.tax_state_tax == 50.00
    assert payroll.tax_local_tax == 10.00
    assert payroll.tax_medicare_tax == 20.00
    assert payroll.tax_social_security == "60.00"
    assert payroll.deduction_sdi == 5.00
    assert payroll.deduction_medical_insurance == 15.00
    assert payroll.deduction_401k == 25.00
    assert payroll.deduction_union_dues == 10.00
    assert payroll.deduction_voluntary == 5.00
    
#passed 
@pytest.mark.django_db
def test_garnishment_order_creation():
    order = models.garnishment_order.objects.create(
        eeid="E1",
        fein="F1",
        work_state="CA",
        type="Child Support",
        amount=100.00,
        arrear_amount=50.00
    )
    assert order.type == "Child Support"
    assert order.amount == 100.00

@pytest.mark.django_db
def test_garnishment_order_required_fields():
    order = models.garnishment_order.objects.create(
        eeid="E2",
        fein="F2",
        work_state="NY",
        type="Tax Levy",
        amount=200.00,
        arrear_amount=100.00
    )
    
    # Test required fields
    assert order.eeid == "E2"
    assert order.fein == "F2"
    assert order.work_state == "NY"
    assert order.type == "Tax Levy"
    assert order.amount == 200.00
    assert order.arrear_amount == 100.00
    assert order.arrear_greater_than_12_weeks is False  # Default value

@pytest.mark.django_db
def test_garnishment_order_optional_fields():
    order = models.garnishment_order.objects.create(
        eeid="E3",
        fein="F3",
        work_state="TX",
        type="Student Loan",
        amount=300.00,
        arrear_amount=150.00,
        # Optional fields
        case_id="CASE123",
        sdu="SDU123",
        start_date="2024-01-01",
        end_date="2024-12-31",
        arrear_greater_than_12_weeks=True
    )
    
    # Test optional fields
    assert order.case_id == "CASE123"
    assert order.sdu == "SDU123"
    assert order.start_date == "2024-01-01"
    assert order.end_date == "2024-12-31"
    assert order.arrear_greater_than_12_weeks is True

@pytest.mark.django_db
def test_garnishment_order_auto_fields():
    order = models.garnishment_order.objects.create(
        eeid="E4",
        fein="F4",
        work_state="FL",
        type="Child Support",
        amount=400.00,
        arrear_amount=200.00
    )
    
    # Test auto-generated fields
    assert order.record_updated is not None
    assert isinstance(order.record_updated, timezone.datetime)

@pytest.mark.django_db
def test_garnishment_order_null_optional_fields():
    # Test creation without optional fields
    order = models.garnishment_order.objects.create(
        eeid="E5",
        fein="F5",
        work_state="WA",
        type="Tax Levy",
        amount=500.00,
        arrear_amount=250.00
    )
    
    # Test that optional fields are null
    assert order.case_id is None
    assert order.sdu is None
    assert order.start_date is None
    assert order.end_date is None

@pytest.mark.django_db
def test_garnishment_order_decimal_precision():
    # Test decimal field precision
    order = models.garnishment_order.objects.create(
        eeid="E6",
        fein="F6",
        work_state="CA",
        type="Child Support",
        amount=123.45,
        arrear_amount=67.89
    )
    
    assert order.amount == 123.45
    assert order.arrear_amount == 67.89


#passed 
@pytest.mark.django_db
def test_iwopdffiles_creation():
    file = models.IWOPDFFiles.objects.create(
        name="Test PDF",
        pdf_url="http://example.com/test.pdf"
    )
    assert file.name == "Test PDF"
    assert file.pdf_url == "http://example.com/test.pdf"
#passed
@pytest.mark.django_db
def test_iwopdffiles_str_method():
    # Test the string representation
    file = models.IWOPDFFiles.objects.create(
        name="Sample IWO",
        pdf_url="http://example.com/sample.pdf"
    )
    assert str(file) == "Sample IWO"
#passed
@pytest.mark.django_db
def test_iwopdffiles_auto_timestamp():
    # Test auto-generated timestamp
    file = models.IWOPDFFiles.objects.create(
        name="Timestamp Test",
        pdf_url="http://example.com/timestamp.pdf"
    )
    assert file.uploaded_at is not None
    assert isinstance(file.uploaded_at, timezone.datetime)

#failed
@pytest.mark.django_db
def test_iwopdffiles_url_validation():
    file = models.IWOPDFFiles.objects.create(
        name="URL Test",
        pdf_url="https://example.com/valid.pdf"
    )
    assert file.pdf_url == "https://example.com/valid.pdf"

    with pytest.raises(Exception):
        models.IWOPDFFiles.objects.create(
            name="Invalid URL",
            pdf_url="not_a_valid_url"
        )



#passed
@pytest.mark.django_db
def test_iwo_details_pdf_creation():
    pdf = models.IWO_Details_PDF.objects.create(
        cid="C1",
        ee_id="E1",
        IWO_Status="Active"
    )
    assert pdf.IWO_Status == "Active"
#passed
@pytest.mark.django_db
def test_iwo_details_pdf_auto_id():
    pdf = models.IWO_Details_PDF.objects.create(
        cid="C2",
        ee_id="E2",
        IWO_Status="Pending"
    )
    assert pdf.IWO_ID is not None
    assert isinstance(pdf.IWO_ID, int)
#passed
@pytest.mark.django_db
def test_iwo_details_pdf_required_fields():
    pdf = models.IWO_Details_PDF.objects.create(
        cid="C3",
        ee_id="E3",
        IWO_Status="Completed"
    )
    
    assert pdf.cid == "C3"
    assert pdf.ee_id == "E3"
    assert pdf.IWO_Status == "Completed"


#passed
@pytest.mark.django_db
def test_iwo_details_pdf_multiple_records():
    pdf1 = models.IWO_Details_PDF.objects.create(
        cid="C4",
        ee_id="E4",
        IWO_Status="Active"
    )
    
    pdf2 = models.IWO_Details_PDF.objects.create(
        cid="C5",
        ee_id="E5",
        IWO_Status="Pending"
    )
    pdf3 = models.IWO_Details_PDF.objects.create(
        cid='c5',
        ee_id='e5',
        IWO_Status='completed'
    )
    
    assert pdf1.IWO_ID != pdf2.IWO_ID != pdf3.IWO_ID #id's should be different
    assert pdf1.cid != pdf2.cid != pdf3.cid
    assert pdf1.ee_id != pdf2.ee_id != pdf3.ee_id
    assert pdf1.IWO_Status != pdf2.IWO_Status != pdf3.IWO_Status

#passed
@pytest.mark.django_db
def test_setting_creation():
    setting = models.setting.objects.create(
        employer_id=1,
        modes=True,
        visibilitys=False
    )
    assert setting.employer_id == 1
    assert setting.modes is True
#passed
@pytest.mark.django_db
def test_setting_boolean_fields():
    # Test different boolean combinations
    setting1 = models.setting.objects.create(
        employer_id=2,
        modes=True,
        visibilitys=True
    )
    assert setting1.modes is True
    assert setting1.visibilitys is True

    setting2 = models.setting.objects.create(
        employer_id=3,
        modes=False,
        visibilitys=False
    )
    assert setting2.modes is False
    assert setting2.visibilitys is False

    setting3 = models.setting.objects.create(
        employer_id=4,
        modes=True,
        visibilitys=False
    )
    assert setting3.modes is True
    assert setting3.visibilitys is False
#passed
@pytest.mark.django_db
def test_setting_auto_timestamp():
    # Test auto-generated timestamp
    setting = models.setting.objects.create(
        employer_id=5,
        modes=True,
        visibilitys=True
    )
    assert setting.timestamp is not None
    assert isinstance(setting.timestamp, timezone.datetime)
#passed
@pytest.mark.django_db
def test_setting_employer_id():
    # Test different employer IDs
    setting1 = models.setting.objects.create(
        employer_id=100,
        modes=True,
        visibilitys=True
    )
    assert setting1.employer_id == 100

    setting2 = models.setting.objects.create(
        employer_id=999999,
        modes=True,
        visibilitys=True
    )
    assert setting2.employer_id == 999999
#passed
@pytest.mark.django_db
def test_setting_multiple_records():
    # Test creating multiple settings for different employers
    settings = []
    for i in range(3):
        setting = models.setting.objects.create(
            employer_id=i + 1,
            modes=True,
            visibilitys=True
        )
        settings.append(setting)
    
    # Verify each setting has unique employer_id
    employer_ids = [s.employer_id for s in settings]
    assert len(set(employer_ids)) == len(settings)  # All IDs should be unique
    
    # Verify timestamps are different
    timestamps = [s.timestamp for s in settings]
    assert len(set(timestamps)) == len(settings)  # All timestamps should be unique


#passed
@pytest.mark.django_db
def test_garnishment_fees_states_rule_creation():
    rule = models.garnishment_fees_states_rule.objects.create(
        state="CA",
        pay_period="Monthly",
        rule="Rule1"
    )
    assert rule.state == "CA"
    assert rule.rule == "Rule1"
#passed
@pytest.mark.django_db
def test_garnishment_fees_states_rule_fields():
    # Test with different values
    rule = models.garnishment_fees_states_rule.objects.create(
        state="NY",
        pay_period="Biweekly",
        rule="Standard Deduction"
    )
    
    assert rule.state == "NY"
    assert rule.pay_period == "Biweekly"
    assert rule.rule == "Standard Deduction"
#passed
#passing differnet pay periods
@pytest.mark.django_db
def test_garnishment_fees_states_rule_pay_periods():
    pay_periods = ["Weekly", "Biweekly", "Monthly", "Semimonthly"]
    
    for period in pay_periods:
        rule = models.garnishment_fees_states_rule.objects.create(
            state="TX",
            pay_period=period,
            rule=f"Rule for {period}"
        )
        assert rule.pay_period == period
#passed
#passing multiple rules for same state
@pytest.mark.django_db
def test_garnishment_fees_states_rule_multiple():
    state = "FL"
    rules_data = [
        ("Weekly", "Rule A"),
        ("Biweekly", "Rule B"),
        ("Monthly", "Rule C")
    ]
    
    created_rules = []
    for pay_period, rule in rules_data:
        rule_obj = models.garnishment_fees_states_rule.objects.create(
            state=state,
            pay_period=pay_period,
            rule=rule
        )
        created_rules.append(rule_obj)
    
    # Verify all rules
    for rule_obj, (pay_period, rule) in zip(created_rules, rules_data):
        assert rule_obj.state == state
        assert rule_obj.pay_period == pay_period
        assert rule_obj.rule == rule
#passed
#testing maximum field lengths

@pytest.mark.django_db
def test_garnishment_fees_states_rule_max_length():
    max_length_str = "X" * 255
    
    rule = models.garnishment_fees_states_rule.objects.create(
        state=max_length_str,
        pay_period=max_length_str,
        rule=max_length_str
    )
    
    assert len(rule.state) == 255
    assert len(rule.pay_period) == 255
    assert len(rule.rule) == 255


#passed
#testing for model creation
@pytest.mark.django_db
def test_garnishment_fees_rules_creation():
    rule = models.garnishment_fees_rules.objects.create(
        rule="Rule1",
        maximum_fee_deduction="100",
        per_pay_period=10.00,
        per_month=40.00,
        per_remittance=5.00
    )
    assert rule.rule == "Rule1"
    assert rule.per_month == 40.00
#passed
#testing for decimal precision only
@pytest.mark.django_db
def test_garnishment_fees_rules_decimal_precision():
    # Test decimal precision
    rule = models.garnishment_fees_rules.objects.create(
        rule="Precision Test",
        maximum_fee_deduction="200",
        per_pay_period=15.75,
        per_month=63.25,
        per_remittance=7.50
    )
    
    assert rule.per_pay_period == 15.75
    assert rule.per_month == 63.25
    assert rule.per_remittance == 7.50
#passed
#testing of garnishment fees rules with large numbers
@pytest.mark.django_db
def test_garnishment_fees_rules_large_numbers():
    rule = models.garnishment_fees_rules.objects.create(
        rule="Large Numbers",
        maximum_fee_deduction="1000",
        per_pay_period=999.99,
        per_month=3999.99,
        per_remittance=499.99
    )
    
    assert rule.per_pay_period == 999.99
    assert rule.per_month == 3999.99
    assert rule.per_remittance == 499.99
#passed
#testint with zero values
@pytest.mark.django_db
def test_garnishment_fees_rules_zero_values():
    # Test with zero values
    rule = models.garnishment_fees_rules.objects.create(
        rule="Zero Values",
        maximum_fee_deduction="0",
        per_pay_period=0.00,
        per_month=0.00,
        per_remittance=0.00
    )
    
    assert rule.per_pay_period == 0.00
    assert rule.per_month == 0.00
    assert rule.per_remittance == 0.00
#passed
#testing with multiple ruels
@pytest.mark.django_db
def test_garnishment_fees_rules_multiple():
    rules_data = [
        {
            "rule": "Rule A",
            "maximum_fee_deduction": "100",
            "per_pay_period": 10.00,
            "per_month": 40.00,
            "per_remittance": 5.00
        },
        {
            "rule": "Rule B",
            "maximum_fee_deduction": "200",
            "per_pay_period": 20.00,
            "per_month": 80.00,
            "per_remittance": 10.00
        }
    ]
    
    created_rules = []
    for data in rules_data:
        rule = models.garnishment_fees_rules.objects.create(**data)
        created_rules.append(rule)
    
    #verifing all rules
    for rule, expected_data in zip(created_rules, rules_data):
        assert rule.rule == expected_data["rule"]
        assert rule.maximum_fee_deduction == expected_data["maximum_fee_deduction"]
        assert rule.per_pay_period == expected_data["per_pay_period"]
        assert rule.per_month == expected_data["per_month"]
        assert rule.per_remittance == expected_data["per_remittance"]


#passed
#model creation
@pytest.mark.django_db
def test_disposable_earning_rules_creation():
    rule = models.disposable_earning_rules.objects.create(
        state="CA",
        disposable_earnings="1000"
    )
    assert rule.state == "CA"
    assert rule.disposable_earnings == "1000"
#failed
#for required fields
@pytest.mark.django_db
def test_disposable_earning_rules_required_fields():
    """Test that both fields are required"""
    with pytest.raises(Exception):
        models.disposable_earning_rules.objects.create(state="CA")
    with pytest.raises(Exception):
        models.disposable_earning_rules.objects.create(disposable_earnings="1000")
#passed
#for multiple rules
@pytest.mark.django_db
def test_disposable_earning_rules_multiple():
    """Test creating multiple rules for different states"""
    rule1 = models.disposable_earning_rules.objects.create(
        state="CA",
        disposable_earnings="1000"
    )
    rule2 = models.disposable_earning_rules.objects.create(
        state="NY",
        disposable_earnings="1200"
    )
    assert models.disposable_earning_rules.objects.count() == 2
    assert rule1.state != rule2.state
    assert rule1.disposable_earnings != rule2.disposable_earnings
#passed
#for the max lenght
@pytest.mark.django_db
def test_disposable_earning_rules_max_length():
    """Test maximum length of fields"""
    long_state = "A" * 255
    long_earnings = "1" * 255
    
    rule = models.disposable_earning_rules.objects.create(
        state=long_state,
        disposable_earnings=long_earnings
    )
    assert len(rule.state) == 255
    assert len(rule.disposable_earnings) == 255
#passed
#for rules with different formats
@pytest.mark.django_db
def test_disposable_earning_rules_different_formats():
    """Test different formats of disposable earnings values"""
    formats = [
        "1000",
        "1,000",
        "1000.00",
        "$1000",
        "1000 USD"
    ]
    
    for earnings in formats:
        rule = models.disposable_earning_rules.objects.create(
            state="CA",
            disposable_earnings=earnings
        )
        assert rule.disposable_earnings == earnings