from User_app.exception_handler import log_and_handle_exceptions
from rest_framework import status
from ..models import (garnishment_fees_states_rule,
                      state_tax_levy_rule, state_tax_levy_rule_edit_permission, state_tax_levy_exempt_amt_config, state_tax_levy_applied_rule)
from django.core.exceptions import ValidationError
from GarnishEdge_Project.garnishment_library.utility_class import ResponseHelper
import logging
from GarnishEdge_Project.garnishment_library.gar_resused_classes import StateAbbreviations
from ..serializers import (GarnishmentFeesStatesRuleSerializer,
                           StateTaxLevyRulesSerializers, StateTaxLevyConfigSerializers, StateTaxLevyExemptAmtConfigSerializers, StateTaxLevyRuleEditPermissionSerializers)
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

logger = logging.getLogger(__name__)


class GarnishmentFeesRulesByState(APIView):
    """
    API view for CRUD operations on garnishment fees rules by state.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Garnishment fees data fetched successfully', GarnishmentFeesStatesRuleSerializer),
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def get(self, request, state=None):
        """
        Retrieve garnishment fees rules for a specific state or all states.
        """
        try:
            if state:
                try:
                    employee = garnishment_fees_states_rule.objects.get(
                        state__iexact=state)
                    serializer = GarnishmentFeesStatesRuleSerializer(
                        employee)
                    return ResponseHelper.success_response('Garnishment fees data fetched successfully', serializer.data)
                except garnishment_fees_states_rule.DoesNotExist:
                    return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
            else:
                employees = garnishment_fees_states_rule.objects.all()
                serializer = GarnishmentFeesStatesRuleSerializer(
                    employees, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)
        except Exception as e:
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=GarnishmentFeesStatesRuleSerializer,
        responses={
            201: openapi.Response('Data created successfully', GarnishmentFeesStatesRuleSerializer),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new garnishment fees rule for a state.
        """
        try:
            serializer = GarnishmentFeesStatesRuleSerializer(
                data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=GarnishmentFeesStatesRuleSerializer,
        responses={
            200: openapi.Response('Data updated successfully', GarnishmentFeesStatesRuleSerializer),
            400: 'State is required in URL to update data or invalid data',
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def put(self, request, state=None):
        """
        Update garnishment fees rule for a specific state.
        """
        if not state:
            return ResponseHelper.error_response('State is required in URL to update data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            employee = garnishment_fees_states_rule.objects.get(
                state__iexact=state)
        except garnishment_fees_states_rule.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        try:
            serializer = GarnishmentFeesStatesRuleSerializer(
                employee, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data updated successfully', serializer.data)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while updating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={
            200: 'State deleted successfully',
            400: 'State is required in URL to delete data',
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def delete(self, request, state=None):
        """
        Delete garnishment fees rule for a specific state.
        """
        if not state:
            return ResponseHelper.error_response('State is required in URL to delete data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            employee = garnishment_fees_states_rule.objects.get(
                state__iexact=state)
            employee.delete()
            return ResponseHelper.success_response(f'State "{state}" deleted successfully')
        except garnishment_fees_states_rule.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while deleting data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StateTaxLevyConfigAPIView(APIView):
    """
    API view for CRUD operations on state tax levy configuration.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('State tax levy config data fetched successfully', StateTaxLevyConfigSerializers),
            404: 'State not found',
            400: 'Invalid input',
            500: 'Internal server error'
        }
    )
    def get(self, request, state=None):
        """
        Retrieve state tax levy config for a specific state or all states.
        """
        try:
            if state:
                state = StateAbbreviations(
                    state.strip()).get_state_name_and_abbr()
                try:
                    rule = state_tax_levy_rule.objects.get(
                        state__iexact=state.strip())
                    serializer = StateTaxLevyConfigSerializers(rule)
                    return ResponseHelper.success_response(f'Data for state "{state}" fetched successfully', serializer.data)
                except state_tax_levy_rule.DoesNotExist:
                    return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
            else:
                rules = state_tax_levy_rule.objects.all()
                serializer = StateTaxLevyConfigSerializers(rules, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)
        except ValidationError as e:
            return ResponseHelper.error_response(f"Invalid input: {str(e)}", status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                "Unexpected error in GET method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=StateTaxLevyConfigSerializers,
        responses={
            201: openapi.Response('Data created successfully', StateTaxLevyConfigSerializers),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new state tax levy config.
        """
        try:
            serializer = StateTaxLevyConfigSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                "Unexpected error in POST method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=StateTaxLevyConfigSerializers,
        responses={
            200: openapi.Response('Data updated successfully', StateTaxLevyConfigSerializers),
            400: 'State and pay_period are required in URL to update data or invalid data',
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    @log_and_handle_exceptions
    def put(self, request, state=None):
        """
        Update state tax levy config for a specific state.
        """
        if not state:
            return ResponseHelper.error_response('State and pay_period are required in URL to update data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            state = StateAbbreviations(
                state.strip()).get_state_name_and_abbr().lower()
            rule = state_tax_levy_rule.objects.get(state__iexact=state)
        except state_tax_levy_rule.DoesNotExist:
            return ResponseHelper.error_response(f'Data for state "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        try:
            serializer = StateTaxLevyConfigSerializers(rule, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data updated successfully', serializer.data)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error updating StateTaxLevyConfigSerializers")
            return ResponseHelper.error_response('Internal server error while updating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={
            200: 'State tax levy config deleted successfully',
            400: 'State is required in URL to delete data',
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def delete(self, request, state=None):
        """
        Delete state tax levy config for a specific state.
        """
        if not state:
            return ResponseHelper.error_response('State is required in URL to delete data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            state_tax_rule = state_tax_levy_rule.objects.get(
                state__iexact=state)
            state_tax_rule.delete()
            return ResponseHelper.success_response(f'Data for state "{state}" deleted successfully')
        except state_tax_levy_rule.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(
                "Unexpected error in DELETE method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Internal server error while deleting data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StateTaxLevyExemptAmtConfigAPIView(APIView):
    """
    API view for CRUD operations on state tax levy exempt amount configuration.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('State tax levy exempt amount config data fetched successfully', StateTaxLevyExemptAmtConfigSerializers(many=True)),
            404: 'State or pay_period not found',
            400: 'Invalid input',
            500: 'Internal server error'
        }
    )
    def get(self, request, state=None, pay_period=None):
        """
        Retrieve state tax levy exempt amount config for a specific state/pay_period or all.
        """
        try:
            if state and pay_period:
                state = StateAbbreviations(
                    state.strip()).get_state_name_and_abbr()
                try:
                    rule = state_tax_levy_exempt_amt_config.objects.filter(
                        state__iexact=state.strip(), pay_period__iexact=pay_period
                    )
                    serializer = StateTaxLevyExemptAmtConfigSerializers(
                        rule, many=True)
                    return ResponseHelper.success_response(
                        f'Data for state "{state}" and pay_period "{pay_period}" fetched successfully',
                        serializer.data
                    )
                except state_tax_levy_exempt_amt_config.DoesNotExist:
                    return ResponseHelper.error_response(
                        f'State "{state}" and pay_period "{pay_period}" not found',
                        status_code=status.HTTP_404_NOT_FOUND
                    )

            elif state:
                state = StateAbbreviations(
                    state.strip()).get_state_name_and_abbr()
                try:
                    rule = state_tax_levy_exempt_amt_config.objects.filter(
                        state__iexact=state.strip())
                    serializer = StateTaxLevyExemptAmtConfigSerializers(
                        rule, many=True)
                    return ResponseHelper.success_response(
                        f'Data for state "{state}" fetched successfully',
                        serializer.data
                    )
                except state_tax_levy_exempt_amt_config.DoesNotExist:
                    return ResponseHelper.error_response(
                        f'State "{state}" not found',
                        status_code=status.HTTP_404_NOT_FOUND
                    )

            else:
                rules = state_tax_levy_exempt_amt_config.objects.all()
                serializer = StateTaxLevyExemptAmtConfigSerializers(
                    rules, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)

        except ValidationError as e:
            return ResponseHelper.error_response(f"Invalid input: {str(e)}", status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                "Unexpected error in GET method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=StateTaxLevyExemptAmtConfigSerializers,
        responses={
            201: openapi.Response('Data created successfully', StateTaxLevyExemptAmtConfigSerializers),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new state tax levy exempt amount config.
        """
        try:
            serializer = StateTaxLevyExemptAmtConfigSerializers(
                data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                "Unexpected error in POST method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=StateTaxLevyExemptAmtConfigSerializers,
        responses={
            200: openapi.Response('Data updated successfully', StateTaxLevyExemptAmtConfigSerializers),
            400: 'State is required in URL to update data or invalid data',
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def put(self, request, state=None, pay_period=None):
        """
        Update state tax levy exempt amount config for a specific state and pay_period.
        """
        if not state and pay_period:
            return ResponseHelper.error_response('State is required in URL to update data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            state_tax_rule = state_tax_levy_exempt_amt_config.objects.get(
                state__iexact=state, pay_period__iexact=pay_period)
        except state_tax_levy_exempt_amt_config.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        try:
            serializer = StateTaxLevyExemptAmtConfigSerializers(
                state_tax_rule, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data updated successfully', serializer.data)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                "Unexpected error in PUT method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Internal server error while updating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={
            200: 'State tax levy exempt amount config deleted successfully',
            400: 'State is required in URL to delete data',
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def delete(self, request, state=None):
        """
        Delete state tax levy exempt amount config for a specific state.
        """
        if not state:
            return ResponseHelper.error_response('State is required in URL to delete data', status_code=status.HTTP_400_BAD_REQUEST)
        try:
            state_tax_rule = state_tax_levy_exempt_amt_config.objects.get(
                state__iexact=state)
            state_tax_rule.delete()
            return ResponseHelper.success_response(f'Data for state "{state}" deleted successfully')
        except state_tax_levy_exempt_amt_config.DoesNotExist:
            return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(
                "Unexpected error in DELETE method of StateTaxLevyConfigAPIView")
            return ResponseHelper.error_response('Internal server error while deleting data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StateTaxLevyAppliedRuleAPIView(APIView):
    """
    API view to get applied state tax levy rule by case_id.
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response('State tax levy applied rule data fetched successfully', StateTaxLevyRulesSerializers),
            404: 'case_id not found',
            400: 'Invalid input provided',
            500: 'Internal server error'
        }
    )
    def get(self, request, case_id):
        """
        Retrieve applied state tax levy rule for a specific case_id.
        """
        try:
            rule = state_tax_levy_applied_rule.objects.get(case_id=case_id)
            serializer = StateTaxLevyRulesSerializers(rule)
            return ResponseHelper.success_response(
                f'Data for case_id "{case_id}" fetched successfully',
                serializer.data
            )
        except state_tax_levy_applied_rule.DoesNotExist:
            return ResponseHelper.error_response(
                f'case_id "{case_id}" not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ValidationError:
            return ResponseHelper.error_response(
                "Invalid input provided",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return ResponseHelper.error_response(
                "An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StateTaxLevyRuleEditPermissionAPIView(APIView):
    """
    API view for CRUD operations on state tax levy rule edit permissions.
    """

    @swagger_auto_schema(
        request_body=StateTaxLevyRuleEditPermissionSerializers,
        responses={
            201: openapi.Response('Data created successfully', StateTaxLevyRuleEditPermissionSerializers),
            400: 'Invalid data',
            500: 'Internal server error'
        }
    )
    def post(self, request):
        """
        Create a new state tax levy rule edit permission.
        """
        try:
            serializer = StateTaxLevyRuleEditPermissionSerializers(
                data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseHelper.success_response('Data created successfully', serializer.data, status_code=status.HTTP_201_CREATED)
            else:
                return ResponseHelper.error_response('Invalid data', serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return ResponseHelper.error_response('Internal server error while creating data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('State tax levy rule edit permission data fetched successfully', StateTaxLevyRuleEditPermissionSerializers(many=True)),
            404: 'State not found',
            500: 'Internal server error'
        }
    )
    def get(self, request, state=None):
        """
        Retrieve state tax levy rule edit permissions for a specific state or all.
        """
        try:
            if state:
                try:
                    state = StateAbbreviations(
                        state.strip()).get_state_name_and_abbr().title()
                    rule = state_tax_levy_rule_edit_permission.objects.get(
                        state__iexact=state)
                    serializer = StateTaxLevyRuleEditPermissionSerializers(
                        rule)
                    return ResponseHelper.success_response(f'Data for state "{state}" fetched successfully', serializer.data)
                except state_tax_levy_rule_edit_permission.DoesNotExist:
                    return ResponseHelper.error_response(f'State "{state}" not found', status_code=status.HTTP_404_NOT_FOUND)
            else:
                rules = state_tax_levy_rule_edit_permission.objects.all()
                serializer = StateTaxLevyRuleEditPermissionSerializers(
                    rules, many=True)
                return ResponseHelper.success_response('All data fetched successfully', serializer.data)
        except Exception as e:
            return ResponseHelper.error_response('Failed to fetch data', str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
