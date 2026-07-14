from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from myapp.models import Product
from .cart import Cart
from .views import parse_positive_int


def cart_payload(cart):
    """One JSON shape for every cart response - the frontend can replace
    its cart state with any of these responses, no special cases."""
    items = []
    for item in cart:
        product = item['product']
        items.append({
            'product_id': product.id,
            'name': product.name,
            'slug': product.slug,
            'image': product.image.url if product.image else None,
            'price': str(item['price']),        # exact decimals as strings,
            'qty': int(item['qty']),
            'line_total': str(item['total']),   # same contract as /api/products/
        })
    return {
        'items': items,
        'total_qty': len(cart),
        'total_price': str(cart.get_total_price()),
    }


# DRF switches off Django's automatic CSRF check and only re-enables it for
# logged-in users. A session cart belongs to guests too, and forging a POST
# that fills someone's cart is exactly what CSRF is - so we protect all of it.
@method_decorator(csrf_protect, name='dispatch')
class CartAPIView(APIView):
    """GET /api/cart/ reads the cart, POST /api/cart/ adds an item."""

    def get(self, request):
        return Response(cart_payload(Cart(request)))

    def post(self, request):
        product_id = parse_positive_int(request.data.get('product_id'))
        qty = parse_positive_int(request.data.get('qty'))
        if product_id is None or qty is None:
            return Response({'error': 'Invalid product or quantity'},
                            status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, id=product_id)
        cart = Cart(request)
        cart.add(product=product, product_qty=qty)
        return Response(cart_payload(cart), status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name='dispatch')
class CartItemAPIView(APIView):
    """PATCH /api/cart/<product_id>/ changes quantity, DELETE removes it."""

    def patch(self, request, product_id):
        cart = Cart(request)
        if str(product_id) not in cart.cart:
            return Response({'error': 'Not in cart'},
                            status=status.HTTP_404_NOT_FOUND)
        qty = parse_positive_int(request.data.get('qty'))
        if qty is None:
            return Response({'error': 'Invalid quantity'},
                            status=status.HTTP_400_BAD_REQUEST)
        cart.update(product=product_id, qty=qty)
        return Response(cart_payload(cart))

    def delete(self, request, product_id):
        cart = Cart(request)
        # removing something already gone is a harmless no-op (same as HTML view)
        cart.delete(product_id=product_id)
        return Response(cart_payload(cart))
