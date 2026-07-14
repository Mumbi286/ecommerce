from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from myapp.models import Product
from .forms import AddressForm
from .models import Address, Order


def make_product(name='Ceramic Mug'):
    return Product.objects.create(
        name=name, price=350, description='A test product',
        image='images/test.jpg', stock=10, active=True,
    )


def valid_address_data(**overrides):
    """A complete, valid form submission; tests override single fields
    to prove that exactly that field gets rejected."""
    data = {
        'full_name': 'Jane Wanjiku',
        'phone': '0712345678',
        'phone_alt': '',
        'delivery_details': 'Greenhouse Apartments, Ngong Road',
        'city': 'Nairobi',
        'county': 'Nairobi',
        'postal_code': '00100',
    }
    data.update(overrides)
    return data


class AddressFormTests(TestCase):
    def test_valid_data_passes(self):
        self.assertTrue(AddressForm(valid_address_data()).is_valid())

    def test_phone_starting_with_0_is_normalized_to_plus254(self):
        form = AddressForm(valid_address_data(phone='0712345678'))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['phone'], '+254712345678')

    def test_foreign_phone_is_rejected(self):
        form = AddressForm(valid_address_data(phone='+15551234567'))
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_postal_code_must_be_five_digits(self):
        form = AddressForm(valid_address_data(postal_code='123'))
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)

    def test_full_name_needs_first_and_last_name(self):
        form = AddressForm(valid_address_data(full_name='Jane'))
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)


class AddressViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123')

    def login(self):
        self.client.login(username='wanjiku', password='a-strong-pass-123')

    def test_add_address_requires_login(self):
        response = self.client.get(reverse('add_address'))
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('add_address'))

    def test_saving_twice_updates_instead_of_duplicating(self):
        self.login()
        self.client.post(reverse('add_address'), valid_address_data())
        self.client.post(reverse('add_address'),
                         valid_address_data(city='Mombasa', county='Mombasa'))
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Address.objects.get(user=self.user).city, 'Mombasa')

    def test_invalid_submission_shows_the_error_on_the_page(self):
        self.login()
        response = self.client.post(
            reverse('add_address'), valid_address_data(postal_code='12'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kenyan postal codes are exactly 5 digits')


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123')
        self.product = make_product()

    def login(self):
        self.client.login(username='wanjiku', password='a-strong-pass-123')

    def fill_cart(self, qty=2):
        self.client.post(reverse('cart_add'), {
            'product_id': self.product.id, 'product_quantity': qty})

    def test_checkout_requires_login(self):
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('checkout'))

    def test_empty_cart_is_bounced_back_to_the_cart_page(self):
        self.login()
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, reverse('cart-overview'))

    def test_checkout_shows_the_saved_address(self):
        self.login()
        self.fill_cart()
        Address.objects.create(
            user=self.user, full_name='Jane Wanjiku', phone='+254712345678',
            delivery_details='Ngong Road', city='Nairobi', county='Nairobi',
            postal_code='00100')
        response = self.client.get(reverse('checkout'))
        self.assertContains(response, 'Jane Wanjiku')


class PlaceOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123')
        self.product = make_product()

    def save_address(self):
        return Address.objects.create(
            user=self.user, full_name='Jane Wanjiku', phone='+254712345678',
            delivery_details='Greenhouse Apartments, Ngong Road',
            city='Nairobi', county='Nairobi', postal_code='00100')

    def login(self):
        self.client.login(username='wanjiku', password='a-strong-pass-123')

    def fill_cart(self, qty=2):
        self.client.post(reverse('cart_add'), {
            'product_id': self.product.id, 'product_quantity': qty})

    def test_place_order_requires_login(self):
        response = self.client.post(reverse('place-order'))
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('place-order'))

    def test_empty_cart_cannot_place_an_order(self):
        self.login()
        response = self.client.post(reverse('place-order'))
        self.assertFalse(response.json()['success'])
        self.assertEqual(Order.objects.count(), 0)

    def test_order_is_created_from_the_cart_and_the_cart_is_cleared(self):
        self.login()
        self.save_address()
        self.fill_cart(qty=2)
        response = self.client.post(reverse('place-order'))
        self.assertTrue(response.json()['success'])
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_amount, Decimal('700'))
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(self.client.session['cart'], {})

    def test_order_without_an_address_is_refused(self):
        self.login()
        self.fill_cart(qty=2)
        response = self.client.post(reverse('place-order'))
        self.assertFalse(response.json()['success'])
        self.assertIn('address', response.json()['message'])
        self.assertEqual(Order.objects.count(), 0)

    def test_order_snapshots_the_delivery_address(self):
        self.login()
        self.save_address()
        self.fill_cart(qty=2)
        self.client.post(reverse('place-order'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.full_name, 'Jane Wanjiku')
        self.assertEqual(order.phone, '+254712345678')
        self.assertEqual(order.county, 'Nairobi')
        self.assertEqual(order.country, 'Kenya')

    def test_editing_the_address_later_does_not_rewrite_the_order(self):
        self.login()
        address = self.save_address()
        self.fill_cart(qty=2)
        self.client.post(reverse('place-order'))
        # the user moves from Nairobi to Mombasa AFTER ordering
        address.city = 'Mombasa'
        address.county = 'Mombasa'
        address.save()
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.county, 'Nairobi')   # history is frozen


class CsrfProtectionTests(TestCase):
    def test_place_order_without_csrf_token_is_rejected(self):
        # the normal test client skips CSRF checks; this one enforces them
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('place-order'))
        self.assertEqual(response.status_code, 403)


class OrderAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123')
        self.product = make_product()

    def login(self):
        self.client.login(username='wanjiku', password='a-strong-pass-123')

    def save_address(self):
        return Address.objects.create(
            user=self.user, full_name='Jane Wanjiku', phone='+254712345678',
            delivery_details='Greenhouse Apartments, Ngong Road',
            city='Nairobi', county='Nairobi', postal_code='00100')

    def fill_cart(self, qty=2):
        self.client.post(reverse('cart_add'), {
            'product_id': self.product.id, 'product_quantity': qty})

    def test_anonymous_user_gets_json_403_not_a_redirect(self):
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, 403)
        self.assertIn('detail', response.json())

    def test_post_creates_the_order_and_returns_it(self):
        self.login()
        self.save_address()
        self.fill_cart(qty=2)
        response = self.client.post('/api/orders/')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['total_amount'], '700.00')
        self.assertEqual(data['county'], 'Nairobi')          # frozen snapshot
        item = data['items'][0]
        self.assertEqual(item['name'], self.product.name)
        self.assertEqual(item['quantity'], 2)
        self.assertEqual(item['line_total'], '700.00')
        self.assertEqual(self.client.session['cart'], {})    # cart cleared

    def test_post_with_an_empty_cart_is_refused(self):
        self.login()
        self.save_address()
        response = self.client.post('/api/orders/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_post_without_an_address_is_refused(self):
        self.login()
        self.fill_cart(qty=2)
        response = self.client.post('/api/orders/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('address', response.json()['error'])

    def test_history_is_paginated_and_only_shows_your_own_orders(self):
        other = User.objects.create_user('otieno', 'o@example.com', 'pass-456-strong')
        Order.objects.create(user=other, total_amount=100)
        self.login()
        self.save_address()
        self.fill_cart(qty=2)
        self.client.post('/api/orders/')
        data = self.client.get('/api/orders/').json()
        self.assertEqual(data['count'], 1)                   # not the other user's
        self.assertEqual(data['results'][0]['total_amount'], '700.00')

    def test_post_without_csrf_token_is_rejected(self):
        # DRF enforces CSRF for session-authenticated users - prove it
        client = Client(enforce_csrf_checks=True)
        client.login(username='wanjiku', password='a-strong-pass-123')
        response = client.post('/api/orders/')
        self.assertEqual(response.status_code, 403)
