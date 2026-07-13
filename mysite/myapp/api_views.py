from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer


class ProductListAPIView(generics.ListAPIView):
    # pagination needs a guaranteed order - without order_by, the database
    # is free to return rows in any order, so pages could repeat or skip items
    queryset = Product.objects.order_by('id')
    serializer_class = ProductSerializer


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # look products up by slug (like the HTML site), not by numeric id
    lookup_field = 'slug'
