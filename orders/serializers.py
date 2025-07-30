from rest_framework import serializers
from .models import Order, Address, OrderItem, OrderAddress

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['name', 'company', 'street1', 'city', 'state', 'postal_code', 'country', 'phone', 'residential']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['parent_order', 'sku', 'name', 'quantity', 'unit_price', 'weight_value', 'weight_units']

class OrderCreateSerializer(serializers.ModelSerializer):
    bill_to = AddressSerializer()
    ship_to = AddressSerializer()
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['order_number', 'order_date', 'order_status', 'customer_email', 'bill_to', 'ship_to', 'items']

    def create(self, validated_data):
        bill_to_data = validated_data.pop('bill_to')
        ship_to_data = validated_data.pop('ship_to')
        items_data = validated_data.pop('items')

        order = Order.objects.create(**validated_data)
        
        bill_address = Address.objects.create(**bill_to_data)
        ship_address = Address.objects.create(**ship_to_data)

        OrderAddress.objects.create(order=order, address=bill_address, address_type='bill_to')
        OrderAddress.objects.create(order=order, address=ship_address, address_type='ship_to')

        for item_data in items_data:
            # Map 'parent_order' to the created order instance
            item_data['parent_order'] = order
            OrderItem.objects.create(**item_data)

        return order