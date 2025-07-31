from rest_framework import serializers
from .models import QuickBooksInvoice

class QuickBooksInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickBooksInvoice
        fields = ['order_number', 'customer_name', 'total_amount', 'status', 'qb_invoice_id', 'created_at', 'updated_at']