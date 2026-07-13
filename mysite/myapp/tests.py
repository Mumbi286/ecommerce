from django.test import TestCase
from django.urls import reverse

from .models import Product


def make_product(name='Ceramic Mug'):
    return Product.objects.create(
        name=name, price=350, description='A test product',
        image='images/test.jpg', stock=10, active=True,
    )


class ProductModelTests(TestCase):
    def test_slug_is_generated_from_the_name(self):
        self.assertEqual(make_product('Blue Shirt').slug, 'blue-shirt')

    def test_two_products_with_the_same_name_get_unique_slugs(self):
        first = make_product('Blue Shirt')
        second = make_product('Blue Shirt')
        self.assertEqual(second.slug, 'blue-shirt-1')
        self.assertNotEqual(first.slug, second.slug)


class ProductPageTests(TestCase):
    def test_home_page_lists_products(self):
        product = make_product()
        response = self.client.get(reverse('index'))
        self.assertContains(response, product.name)

    def test_detail_page_is_reachable_via_slug(self):
        product = make_product()
        response = self.client.get(product.get_absolute_url())
        self.assertContains(response, product.name)
