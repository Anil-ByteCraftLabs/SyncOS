from django.db import models

class QuickBooksInvoice(models.Model):
    qb_invoice_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    order_number = models.CharField(max_length=50, null=False)
    customer_name = models.CharField(max_length=100, null=False)
    total_amount = models.FloatField(null=False)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.order_number} - {self.customer_name}"