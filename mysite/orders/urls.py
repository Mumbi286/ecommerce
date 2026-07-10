from django.urls import path 
from . import views


urlpatterns=[
    path('add-address/',views.add_address,name='add_address'),
    path('checkout/',views.checkout,name='checkout'),
    path('place-order',views.place_order,name='place-order'),
    path('order-success',views.order_success,name='order-success'),
    path('order-failed',views.order_failed,name='order-failed'),
    
]