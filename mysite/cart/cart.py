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

