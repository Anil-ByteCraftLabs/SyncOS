from django.urls import path
from .views import QuickBooksCreateInvoiceView, QuickBooksGetInvoiceView

urlpatterns = [
    path('create-invoice/', QuickBooksCreateInvoiceView.as_view(), name='quickbooks-create-invoice'),
    path('get-invoice/<str:qb_invoice_id>/', QuickBooksGetInvoiceView.as_view(), name='quickbooks-get-invoice'),
]