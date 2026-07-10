from myapp.models import Product
from decimal import Decimal

class Cart():
    def __init__(self,request):
        # creating the session and extracting the session
        self.session = request.session
        cart = request.session.get('cart')
        # Checking if the cart exists in our sessions
        if 'cart' not in request.session:
            # Intializing the empty cart 
            cart = self.session['cart'] = {}
            # else load the existing cart
        self.cart = cart

    def __len__(self):
        return sum (int(item['qty']) for item in self.cart.values())
    
    # calculating the total 
    def get_total_price(self):
        return sum(Decimal(item['price']) * Decimal(item['qty']) for item in self.cart.values())
    
    # converting the cart into iterable
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product']=product

        for item in cart.values():
            item['price']= Decimal(item['price'])
            item['qty']= Decimal(item['qty'])
            item['total']=item['price']*item['qty']
            yield item

        
    
            



# allows us to add items to add in the cart
    def add(self,product,product_qty):
        product_id = product.id
        # checking if the product exists 
        if product_id in self.cart:
            # using a two dimensional data structure
            self.cart[product_id]['qty'] = product_qty
        else:
            self.cart[product_id]={'price':str(product.price),'qty':product_qty} # self.cart[3] = {'price}:str(80),'qty':1}        
        # modifying our session
        self.session.modified = True 

    # delete method 
    def delete(self,product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
        self.session.modified=True # makes sure the cart stored into the session is updated

    def clear(self):
        # empties the whole cart, e.g. right after an order is placed
        self.cart.clear()
        self.session.modified=True

    def update(self,product,qty):
        product_id = str(product)
        product_quantity = qty
        if product_id in self.cart:
            # accessing the cart
            self.cart[product_id]['qty']=product_quantity
        self.session.modified=True

