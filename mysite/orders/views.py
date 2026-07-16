from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import AddressForm
from .models import Address,Order,OrderItem,ADDRESS_SNAPSHOT_FIELDS
from cart.cart import Cart
from django.http import JsonResponse

# Create your views here.
@login_required
def add_address(request):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address=None
    if request.method=="POST":
        # instance=address updates the existing address instead of creating a duplicate
        form = AddressForm(request.POST,instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect("index")
        # invalid form falls through so its error messages are shown on the page
    else:
        form = AddressForm(instance=address)
    return render(request,'orders/add_address.html',{'form':form})

@login_required
def checkout(request):
    # an empty cart has nothing to check out - send the user back to their cart
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart-overview')
    # login_required guarantees a logged-in user, so just fetch their address
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None
    return render(request,'orders/checkout.html',{'address':address})


@login_required
def place_order(request):
    # when this process starts the order success is false
    order_success=False
    # we need to check if the request method is post
    if request.method=="POST":
        #  we need to check the cart instance so as we fetch all items in our cart
        cart = Cart(request)
        # refuse to create an order from an empty cart
        if len(cart) == 0:
            return JsonResponse({'success': False, 'message': 'Your cart is empty'})
        # no address, no delivery - refuse before creating anything
        address = Address.objects.filter(user=request.user).first()
        if address is None:
            return JsonResponse({'success': False,
                                 'message': 'Add a delivery address before placing an order'})
        total_amount = cart.get_total_price()

        # freeze the address onto the order (see ADDRESS_SNAPSHOT_FIELDS)
        snapshot = {field: getattr(address, field) for field in ADDRESS_SNAPSHOT_FIELDS}
        # login_required guarantees a user, so every order is linked to one
        order = Order.objects.create(user=request.user,total_amount=total_amount,**snapshot)
        for item in cart:
            OrderItem.objects.create(order=order,product=item['product'],quantity=item['qty'])
        # the items are now in the order, so the cart starts fresh
        cart.clear()
        order_success= True
    return JsonResponse({'success':order_success})


def order_success(request):
    return render(request,'orders/order-success.html')

def order_failed(request):
    return render(request,'orders/order-failed.html')

