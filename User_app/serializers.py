from rest_framework import serializers
from .models import *
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Employer_Profile
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import serializers
from datetime import datetime


class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        access_token = AccessToken(data['access'])

        # Add expiration time
        data['access_expires'] = access_token['exp']
        # Add human-readable datetime
        data['access_expires_datetime'] = datetime.fromtimestamp(
            access_token['exp']).isoformat()

        return data


class EmployerRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Employer_Profile
        fields = [
            'employer_name', 'username', 'email', 'password1', 'password2',
            'federal_employer_identification_number', 'street_name', 'city',
            'state', 'country', 'zipcode', 'number_of_employees',
            'department', 'location'
        ]

    def validate(self, data):
        password1 = data.get('password1')
        password2 = data.get('password2')

        if password1 != password2:
            raise serializers.ValidationError("Passwords do not match")

        if not (len(password1) >= 8 and any(c.isupper() for c in password1) and
                any(c.islower() for c in password1) and any(c.isdigit() for c in password1) and
                any(c in '!@#$%^&*()_+' for c in password1)):
            raise serializers.ValidationError(
                "Password must meet complexity requirements")

        if Employer_Profile.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already used")

        if Employer_Profile.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already used")

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['password'] = make_password(
            validated_data.pop('password1'))
        return Employer_Profile.objects.create(**validated_data)


class EmployeeDetailsSerializer(serializers.ModelSerializer):

    is_blind = serializers.BooleanField(required=False, allow_null=True)
    support_second_family = serializers.BooleanField(
        required=False, allow_null=True)
    spouse_age = serializers.IntegerField(required=False, allow_null=True)
    is_spouse_blind = serializers.BooleanField(required=False, allow_null=True)

    class Meta:
        model = employee_detail
        fields = '__all__'


class IWOPDFFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IWOPDFFiles
        fields = ['id', 'name', 'pdf_url', 'uploaded_at']


class GarnishmentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = garnishment_order
        fields = '__all__'


class GetEmployerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer_Profile
        fields = '__all__'


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = setting
        fields = '__all__'


class APICallCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class GarnishmentFeesSerializer(serializers.ModelSerializer):
    class Meta:
        model = garnishment_fees
        fields = '__all__'


class GarnishmentFeesStatesRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = garnishment_fees_states_rule
        fields = ['id', 'state', 'pay_period', 'rule']


class GarnishmentFeesRulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = garnishment_fees_rules
        fields = ['id', 'rule', 'maximum_fee_deduction',
                  'per_pay_period', 'per_month', 'per_remittance']


class WithholdingOrderDataSerializers(serializers.ModelSerializer):
    class Meta:
        model = withholding_order_data
        fields = '__all__'


class StateTaxLevyConfigSerializers(serializers.ModelSerializer):
    class Meta:
        model = state_tax_levy_rule
        fields = '__all__'


class StateTaxLevyRulesSerializers(serializers.ModelSerializer):
    class Meta:
        model = state_tax_levy_applied_rule
        exclude = ['id']


class StateTaxLevyRuleEditPermissionSerializers(serializers.ModelSerializer):
    class Meta:
        model = state_tax_levy_rule_edit_permission
        fields = '__all__'


class CreditorDebtAppliedRulesSerializers(serializers.ModelSerializer):
    class Meta:
        model = creditor_debt_applied_rule
        fields = '__all__'


class CreditorDebtExemptAmtConfigSerializers(serializers.ModelSerializer):
    class Meta:
        model = creditor_debt_exempt_amt_config
        fields = '__all__'


class StateTaxLevyExemptAmtConfigSerializers(serializers.ModelSerializer):
    class Meta:
        model = state_tax_levy_exempt_amt_config
        fields = '__all__'


class CreditorDebtRuleSerializers(serializers.ModelSerializer):
    class Meta:
        model = creditor_debt_rule
        fields = '__all__'


class CreditorDebtRuleEditPermissionSerializers(serializers.ModelSerializer):
    class Meta:
        model = creditor_debt_rule_edit_permission
        fields = '__all__'
