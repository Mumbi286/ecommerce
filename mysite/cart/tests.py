from django.test import Client, TestCase
from django.urls import reverse

from myapp.models import Product
from .cart import Cart


class FakeRequest:
    """Cart() only ever touches request.session, so a bare object
    carrying a real session store is enough to test it directly."""
    def __init__(self, session):
        self.session = session


def make_product(name='Ceramic Mug', active=True):
    return Product.objects.create(
        name=name, price=350, description='A test product',
        image='images/test.jpg', stock=10, active=active,
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
        self.assertEqual(self.client.session['cart'][str(self.product.id)]['qty'], 4)

    def test_get_request_is_rejected_with_405(self):
        self.assertEqual(self.client.get(reverse('cart_add')).status_code, 405)

    def test_non_numeric_quantity_is_rejected_with_400(self):
        response = self.client.post(reverse('cart_add'), {
            'product_id': self.product.id, 'product_quantity': 'abc'})
        self.assertEqual(response.status_code, 400)

    def test_unknown_product_returns_404(self):
        response = self.client.post(reverse('cart_add'), {
            'product_id': 99999, 'product_quantity': 1})
        self.assertEqual(response.status_code, 404)

    def test_adding_an_inactive_product_is_refused_with_404(self):
        inactive = make_product('Retired Kettle', active=False)
        response = self.client.post(reverse('cart_add'), {
            'product_id': inactive.id, 'product_quantity': 1})
        self.assertEqual(response.status_code, 404)


class CsrfProtectionTests(TestCase):
    def test_cart_add_without_csrf_token_is_rejected(self):
        # the normal test client skips CSRF checks; this one enforces them
        client = Client(enforce_csrf_checks=True)
        product = make_product()
        response = client.post(reverse('cart_add'), {
            'product_id': product.id, 'product_quantity': 1})
        self.assertEqual(response.status_code, 403)


class CartAPITests(TestCase):
    def setUp(self):
        self.product = make_product()

    def api_add(self, qty=2):
        return self.client.post('/api/cart/', {
            'product_id': self.product.id, 'qty': qty})

    def test_empty_cart_has_the_full_shape(self):
        data = self.client.get('/api/cart/').json()
        self.assertEqual(data, {'items': [], 'total_qty': 0, 'total_price': '0'})

    def test_add_returns_201_and_the_whole_cart(self):
        response = self.api_add(qty=2)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['total_qty'], 2)
        self.assertEqual(data['total_price'], '700.00')     # exact, as a string
        item = data['items'][0]
        self.assertEqual(item['product_id'], self.product.id)
        self.assertEqual(item['price'], '350.00')
        self.assertEqual(item['line_total'], '700.00')

    def test_add_shares_the_session_cart_with_the_html_views(self):
        # the API and the old jQuery endpoints write to the SAME cart
        self.api_add(qty=2)
        response = self.client.post(reverse('cart_delete'), {
            'product_id': self.product.id})
        self.assertEqual(response.json()['qty'], 0)

    def test_add_rejects_a_bad_quantity_with_400(self):
        response = self.client.post('/api/cart/', {
            'product_id': self.product.id, 'qty': 'abc'})
        self.assertEqual(response.status_code, 400)

    def test_add_unknown_product_returns_json_404(self):
        response = self.client.post('/api/cart/', {'product_id': 99999, 'qty': 1})
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.json())            # JSON, not an HTML page

    def test_adding_an_inactive_product_is_refused_with_404(self):
        inactive = make_product('Retired Kettle', active=False)
        response = self.client.post('/api/cart/', {
            'product_id': inactive.id, 'qty': 1})
        self.assertEqual(response.status_code, 404)

    def test_patch_changes_the_quantity(self):
        self.api_add(qty=1)
        response = self.client.patch(
            f'/api/cart/{self.product.id}/', {'qty': 4},
            content_type='application/json')
        self.assertEqual(response.json()['total_qty'], 4)

    def test_patch_a_product_not_in_the_cart_returns_404(self):
        response = self.client.patch(
            f'/api/cart/{self.product.id}/', {'qty': 4},
            content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_the_item(self):
        self.api_add(qty=2)
        response = self.client.delete(f'/api/cart/{self.product.id}/')
        self.assertEqual(response.json(), {
            'items': [], 'total_qty': 0, 'total_price': '0'})

    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post('/api/cart/', {
            'product_id': self.product.id, 'qty': 1})
        self.assertEqual(response.status_code, 403)

    def test_delete_on_the_collection_clears_the_whole_cart(self):
        self.api_add(qty=2)
        other = make_product('Second Item')
        self.client.post('/api/cart/', {'product_id': other.id, 'qty': 1})
        response = self.client.delete('/api/cart/')
        self.assertEqual(response.json(), {
            'items': [], 'total_qty': 0, 'total_price': '0'})
        self.assertEqual(self.client.session['cart'], {})

    def test_clear_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.delete('/api/cart/')
        self.assertEqual(response.status_code, 403)
