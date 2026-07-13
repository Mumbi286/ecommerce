from django.test import Client, TestCase
from django.urls import reverse

from myapp.models import Product
from .cart import Cart


class FakeRequest:
    """Cart() only ever touches request.session, so a bare object
    carrying a real session store is enough to test it directly."""
    def __init__(self, session):
        self.session = session


def make_product(name='Ceramic Mug'):
    return Product.objects.create(
        name=name, price=350, description='A test product',
        image='images/test.jpg', stock=10, active=True,
    )


class CartClassTests(TestCase):
    def test_add_stores_keys_as_strings(self):
        product = make_product()
        cart = Cart(FakeRequest(self.client.session))
        cart.add(product, 2)
        self.assertEqual(list(cart.cart.keys()), [str(product.id)])

    def test_delete_right_after_add_removes_the_item(self):
        product = make_product()
        cart = Cart(FakeRequest(self.client.session))
        cart.add(product, 2)
        cart.delete(product.id)
        self.assertEqual(len(cart), 0)


class CartViewTests(TestCase):
    def setUp(self):
        self.product = make_product()

    def add_to_cart(self, qty):
        return self.client.post(reverse('cart_add'), {
            'product_id': self.product.id, 'product_quantity': qty,
        })

    def test_add_returns_the_badge_quantity(self):
        response = self.add_to_cart(2)
        self.assertEqual(response.json()['qty'], 2)

    def test_adding_the_same_product_again_replaces_instead_of_duplicating(self):
        self.add_to_cart(2)
        response = self.add_to_cart(3)
        # before the fix this returned 5: the old "2" under a string key
        # plus a duplicate entry with qty 3 under an int key
        self.assertEqual(response.json()['qty'], 3)

    def test_delete_removes_the_product(self):
        self.add_to_cart(2)
        response = self.client.post(reverse('cart_delete'), {
            'product_id': self.product.id, 'action': 'post',
        })
        self.assertEqual(response.json()['qty'], 0)

    def test_update_changes_the_quantity(self):
        self.add_to_cart(1)
        self.client.post(reverse('cart_update'), {
            'product_id': self.product.id, 'product_quantity': 4,
        })
        self.assertEqual(self.client.session['cart'][str(self.product.id)]['qty'], '4')


class CsrfProtectionTests(TestCase):
    def test_cart_add_without_csrf_token_is_rejected(self):
        # the normal test client skips CSRF checks; this one enforces them
        client = Client(enforce_csrf_checks=True)
        product = make_product()
        response = client.post(reverse('cart_add'), {
            'product_id': product.id, 'product_quantity': 1})
        self.assertEqual(response.status_code, 403)
