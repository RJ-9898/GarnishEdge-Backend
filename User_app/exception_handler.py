# utils/decorators.py
import traceback
from functools import wraps
from rest_framework import status
from User_app.models import APILog
from GarnishEdge_Project.garnishment_library.utility_class import ResponseHelper


def log_and_handle_exceptions(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        try:
            return view_func(self, request, *args, **kwargs)
        except Exception as e:
            # Attempt to log into APILog
            try:
                APILog.objects.create(
                    api_name=self.__class__.__name__,
                    request_method=request.method,
                    request_url=request.build_absolute_uri(),
                    request_headers=dict(request.headers),
                    request_body=request.body.decode('utf-8', errors='ignore'),
                    status_code=500,
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                    user=str(
                        request.user) if request.user and request.user.is_authenticated else 'Anonymous'
                )
            except Exception as log_err:
                print(f"Log save failed: {log_err}")

            # Use your helper to return the structured response
            return ResponseHelper.error_response(
                message="Internal server error",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return _wrapped_view
