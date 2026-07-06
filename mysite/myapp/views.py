from django.shortcuts import render

from .models import Product


def index(request):
    """Render the home page with a list of all products."""
    products = Product.objects.all()
    return render(request, 'myapp/index.html', {'products': products})


def detail(request, slug):
    """Render the detail page for the product matching the URL slug."""
    product = Product.objects.get(slug=slug)
    return render(request, 'myapp/detail.html', {'product': product})
