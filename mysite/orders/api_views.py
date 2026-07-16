from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.cart import Cart
from .models import Address, Order, OrderItem, ADDRESS_SNAPSHOT_FIELDS
from .serializers import OrderSerializer


class OrderListCreateAPIView(generics.ListAPIView):
    """GET /api/orders/ - own order history. POST /api/orders/ - place
    an order from the session cart (mirrors the HTML place_order view)."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only YOUR orders - the user comes from the session, never the URL
        return (Order.objects.filter(user=self.request.user)
                .order_by('-created_at')
                .prefetch_related('items__product'))

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            return Response({'error': 'Your cart is empty'},
                            status=status.HTTP_400_BAD_REQUEST)
        address = Address.objects.filter(user=request.user).first()
        if address is None:
            return Response({'error': 'Add a delivery address before placing an order'},
                            status=status.HTTP_400_BAD_REQUEST)

        snapshot = {field: getattr(address, field) for field in ADDRESS_SNAPSHOT_FIELDS}
        # all-or-nothing: an order must never exist with half its items
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user, total_amount=cart.get_total_price(), **snapshot)
            for item in cart:
                OrderItem.objects.create(
                    order=order, product=item['product'], quantity=int(item['qty']))
        cart.clear()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
