from django.shortcuts import render, get_object_or_404

from .models import Product


def index(request):
    """Render the home page with a list of all products."""
    products = Product.objects.filter(active=True)
    return render(request, 'myapp/index.html', {'products': products})


def detail(request, slug):
    """Render the detail page for the product matching the URL slug."""
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'myapp/detail.html', {'product': product})
