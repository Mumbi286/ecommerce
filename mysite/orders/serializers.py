from rest_framework import serializers
from .models import Order, OrderItem, ADDRESS_SNAPSHOT_FIELDS


class OrderItemSerializer(serializers.ModelSerializer):
    # flatten the product into what an order line needs - same field
    # names as the cart API, so the frontend renders both the same way
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    name = serializers.CharField(source='product.name', read_only=True)
    slug = serializers.SlugField(source='product.slug', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10,
                                     decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(source='total_price', max_digits=10,
                                          decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product_id', 'name', 'slug', 'price', 'quantity', 'line_total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'total_amount', 'is_paid', 'created_at',
                  *ADDRESS_SNAPSHOT_FIELDS, 'items']
