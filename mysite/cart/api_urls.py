from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.CartAPIView.as_view(), name='api-cart'),
    path('<int:product_id>/', api_views.CartItemAPIView.as_view(), name='api-cart-item'),
]
