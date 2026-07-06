from django.shortcuts import render
from django.http import JsonResponse
from .cart import Cart
from myapp.models import Product
from django.shortcuts import get_object_or_404

# Create your views here.
# adding the product to the cart
def cart_add(request):
    cart = Cart(request) #Creating the cart instance
    print("Add to cart button clicked")
    # checking if the django app is receiving a POST request
    if request.method=="POST":
        # Extracting the request data
        product_id = request.POST.get("product_id")
        product_quantity = request.POST.get("product_quantity")
        print("Product added to the cart has an id:",product_id)
        print("Product quantity is:",product_quantity)
        # product = Product.objects.get(id=product_id)
        product = get_object_or_404(Product,id=product_id)
        cart.add(product=product,product_qty=product_quantity)

    return JsonResponse({'Message':'Add to Cart button clicked'})
