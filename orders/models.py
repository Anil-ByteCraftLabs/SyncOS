from django.db import models

class Address(models.Model):
    name = models.CharField(max_length=100, null=False)
    company = models.CharField(max_length=100, null=True, blank=True)
    street1 = models.CharField(max_length=100, null=False)
    city = models.CharField(max_length=100, null=False)
    state = models.CharField(max_length=50, null=False)
    postal_code = models.CharField(max_length=20, null=False)
    country = models.CharField(max_length=50, null=False)
    phone = models.CharField(max_length=20, null=True, blank=True)
    residential = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.name

class OrderAddress(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=10, choices=[('bill_to', 'Bill To'), ('ship_to', 'Ship To')])

    class Meta:
        unique_together = ('order', 'address', 'address_type')

class OrderItem(models.Model):
    parent_order = models.ForeignKey('Order', on_delete=models.CASCADE)
    sku = models.CharField(max_length=50, null=False)
    name = models.CharField(max_length=100, null=False)
    quantity = models.IntegerField(null=False)
    unit_price = models.FloatField(null=False)
    weight_value = models.FloatField(null=True, blank=True)
    weight_units = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    order_number = models.CharField(max_length=50, unique=True, null=False)
    order_date = models.DateTimeField(null=False)
    order_status = models.CharField(max_length=50, null=False)
    customer_email = models.EmailField(null=False)
    addresses = models.ManyToManyField(Address, through=OrderAddress)
    items = models.ManyToManyField(OrderItem, related_name='related_items')

    def __str__(self):
        return self.order_number