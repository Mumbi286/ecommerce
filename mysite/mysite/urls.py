"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from django.http import JsonResponse
from django.views.defaults import page_not_found, server_error
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def custom_404(request, exception):
    # API callers get JSON errors, never an HTML error page
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'Not found'}, status=404)
    return page_not_found(request, exception)


def custom_500(request):
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'Server error'}, status=500)
    return server_error(request)


handler404 = custom_404
handler500 = custom_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('myapp.urls')),
    path('cart/',include('cart.urls')),
    path('users/',include('users.urls')),
    path('orders/',include('orders.urls')),
    # JSON API - the HTML views above keep working during the transition
    path('api/products/', include('myapp.api_urls')),
    path('api/cart/', include('cart.api_urls')),
    path('api/orders/', include('orders.api_urls')),
    path('api/auth/', include('users.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),

]
urlpatterns+= static(settings.MEDIA_URL,document_root= settings.MEDIA_ROOT)
