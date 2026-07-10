from django.shortcuts import render,redirect
from .forms import AddressForm
from .models import Address,Order,OrderItem
from cart.cart import Cart
from django.http import JsonResponse

# Create your views here.
def add_address(request):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address=None
    if request.method=="POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect("index")
    form = AddressForm(instance=address)
    return render(request,'orders/add_address.html',{'form':form})

def checkout(request):
    # to check if the user is logged in and is also authenticated
    if request.user.is_authenticated:
        try:
            address = Address.objects.get(user=request.user)
            return render(request,'orders/checkout.html',{'address':address})
        except:
            return render(request,'orders/checkout.html')
        else:
            return render(request,'orders/checkout.html')
        

def place_order(request):
    # when this process starts the order success is false 
    order_success=False
    # we need to check if the request method is post
    if request.method=="POST":
        #  we need to check the cart instance so as we fetch all items in our cart
        cart = Cart(request)
        total_amount = cart.get_total_price()


        # checking if the user is authenticated
        if request.user.is_authenticated:
            order = Order.objects.create(user=request.user,total_amount=total_amount)
            for item in cart:
                OrderItem.objects.create(order=order,product=item['product'],quantity=item['qty'])
            order_success= True
        #  if the user is not authenticated, and we will perform the above and the only expection is that we dont want to pass the user
        else:
            order = Order.objects.create(total_amount=total_amount)
            for item in cart:
                OrderItem.objects.create(order=order,product=item['product'],quantity=item['qty'])
            order_success=True
    return JsonResponse({'success':order_success})


def order_success(request):
    return render(request,'orders/order-success.html')

def order_failed(request):
    return render(request,'orders/order-failed.html')

