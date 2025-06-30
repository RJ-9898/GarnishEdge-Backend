from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from debug_toolbar.toolbar import debug_toolbar_urls
from drf_yasg import openapi
from rest_framework import permissions
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="Garnishment API",
        default_version='v1',
        description="API documentation for Garnishment",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('User/',include('User_app.urls.urls')),

    path('APIWebDoc', TemplateView.as_view(
        template_name='doc.html',
        extra_context={'schema_url':'garnishment-schema'}
    ), name='api_doc'),

    # Swagger UI
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # ReDoc UI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('__debug__/', include('debug_toolbar.urls')),
    path('auth/', include('User_app.urls.auth_urls', namespace='auth')),
    path('employee/', include('User_app.urls.employee_urls', namespace='employee')),
    path('employer/', include('User_app.urls.employer_urls', namespace='employer')),
    path('garnishment/', include('User_app.urls.garnishment_urls', namespace='garnishment')),
    path('garnishment_state/', include('User_app.urls.garnishment_state_urls', namespace='garnishment_state')),
    path('garnishment_creditor/', include('User_app.urls.garnishment_creditor_urls', namespace='garnishment_creditor')),
    path('utility/', include('User_app.urls.utility_urls', namespace='utility'))
]


