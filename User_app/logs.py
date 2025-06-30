# app/utils.py (create this file if not exists)

from .models import Logdata

def log_api(api_name, endpoint, status_code, message, status,user_id=None):
    Logdata.objects.create(
        api_name=api_name,
        endpoint=endpoint,
        status_code=status_code,
        message=message,
        status=status,
        user_id=user_id
    )
