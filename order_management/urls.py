from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('orders.urls')),
    path('quickbooks/', include('quickbooks_integration.urls')),
    path('docs/', include_docs_urls(title='Order Management API')),
]