from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Product


def make_product(name='Ceramic Mug', active=True):
    return Product.objects.create(
        name=name, price=350, description='A test product',
        image='images/test.jpg', stock=10, active=active,
    )


class ProductModelTests(TestCase):
    def test_slug_is_generated_from_the_name(self):
        self.assertEqual(make_product('Blue Shirt').slug, 'blue-shirt')

    def test_two_products_with_the_same_name_get_unique_slugs(self):
        first = make_product('Blue Shirt')
        second = make_product('Blue Shirt')
        self.assertEqual(second.slug, 'blue-shirt-1')
        self.assertNotEqual(first.slug, second.slug)

    def test_price_is_stored_as_an_exact_decimal(self):
        product = make_product()
        product.price = Decimal('299.99')
        product.save()
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal('299.99'))
        self.assertIsInstance(product.price, Decimal)


class ProductPageTests(TestCase):
    def test_home_page_lists_products(self):
        product = make_product()
        response = self.client.get(reverse('index'))
        self.assertContains(response, product.name)

    def test_detail_page_is_reachable_via_slug(self):
        product = make_product()
        response = self.client.get(product.get_absolute_url())
        self.assertContains(response, product.name)

    def test_unknown_slug_returns_404_not_a_crash(self):
        response = self.client.get('/no-such-product')
        self.assertEqual(response.status_code, 404)

    def test_inactive_product_is_hidden_from_the_home_page(self):
        make_product('Retired Kettle', active=False)
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'Retired Kettle')

    def test_inactive_product_detail_page_is_a_404(self):
        product = make_product('Retired Kettle', active=False)
        response = self.client.get(product.get_absolute_url())
        self.assertEqual(response.status_code, 404)


class ProductAPITests(TestCase):
    def test_list_returns_paginated_products(self):
        product = make_product()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)                      # pagination shape
        self.assertEqual(data['results'][0]['name'], product.name)
        self.assertEqual(data['results'][0]['price'], '350.00')  # exact, as a string

    def test_detail_is_looked_up_by_slug(self):
        product = make_product()
        response = self.client.get(f'/api/products/{product.slug}/')
        self.assertEqual(response.json()['name'], product.name)

    def test_unknown_slug_returns_json_404(self):
        response = self.client.get('/api/products/no-such-product/')
        self.assertEqual(response.status_code, 404)

    def test_inactive_product_is_excluded_from_the_api_list(self):
        make_product('Visible Mug')
        make_product('Retired Kettle', active=False)
        data = self.client.get('/api/products/').json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Visible Mug')

    def test_inactive_product_api_detail_is_a_404(self):
        product = make_product('Retired Kettle', active=False)
        response = self.client.get(f'/api/products/{product.slug}/')
        self.assertEqual(response.status_code, 404)

    def test_list_is_paginated_at_twelve(self):
        for i in range(13):
            make_product(f'Product {i}')
        data = self.client.get('/api/products/').json()
        self.assertEqual(data['count'], 13)
        self.assertEqual(len(data['results']), 12)   # page 1 is full
        self.assertIsNotNone(data['next'])           # and page 2 exists
