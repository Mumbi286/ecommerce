from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.ProductListAPIView.as_view(), name='api-product-list'),
    path('<slug:slug>/', api_views.ProductDetailAPIView.as_view(), name='api-product-detail'),
]
