from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.OrderListCreateAPIView.as_view(), name='api-orders'),
]
