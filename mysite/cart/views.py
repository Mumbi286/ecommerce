from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from .cart import Cart
from myapp.models import Product


def parse_positive_int(value):
    """Return the value as an int if it is a whole number >= 1,
    otherwise None - AJAX callers must send sane numbers."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 1 else None


def cart_add(request):
    # a stray GET now gets a clear 405 instead of an UnboundLocalError crash
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    product_id = parse_positive_int(request.POST.get("product_id"))
    quantity = parse_positive_int(request.POST.get("product_quantity"))
    if product_id is None or quantity is None:
        return JsonResponse({'error': 'Invalid product or quantity'}, status=400)
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.add(product=product, product_qty=quantity)
    return JsonResponse({'qty': len(cart)})


def cart_overview(request):
    cart = Cart(request)
    return render(request,'cart/cart-overview.html',{'cart':cart})


def cart_delete(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    cart = Cart(request)
    # deleting something that is not in the cart is a harmless no-op
    cart.delete(product_id=request.POST.get('product_id'))
    return JsonResponse({'qty': len(cart), 'total': cart.get_total_price()})


def cart_update(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    quantity = parse_positive_int(request.POST.get('product_quantity'))
    if quantity is None:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)
    cart = Cart(request)
    cart.update(product=request.POST.get('product_id'), qty=quantity)
    return JsonResponse({'qty': len(cart), 'total': cart.get_total_price()})
