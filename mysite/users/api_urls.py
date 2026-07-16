from django.urls import path
from . import api_views

urlpatterns = [
    path('csrf/', api_views.CsrfCookieAPIView.as_view(), name='api-csrf'),
    path('register/', api_views.RegisterAPIView.as_view(), name='api-register'),
    path('verify-email/', api_views.VerifyEmailAPIView.as_view(), name='api-verify-email'),
    path('login/', api_views.LoginAPIView.as_view(), name='api-login'),
    path('logout/', api_views.LogoutAPIView.as_view(), name='api-logout'),
    path('me/', api_views.MeAPIView.as_view(), name='api-me'),
]
