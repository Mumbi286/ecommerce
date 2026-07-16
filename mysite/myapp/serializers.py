from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # 'active' is not exposed: the API only ever serves active products,
        # so the field would be a constant 'true' on every response
        fields = ['id', 'name', 'price', 'description', 'image', 'slug', 'stock']
