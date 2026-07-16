from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .emails import send_verification_email
from .forms import CreateUserForm
from .token import account_activation_token


def user_payload(user):
    return {'id': user.id, 'username': user.username, 'email': user.email}


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfCookieAPIView(APIView):
    """GET /api/auth/csrf/ - the frontend calls this once so the CSRF
    cookie exists before its first POST."""

    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})


@method_decorator(csrf_protect, name='dispatch')
class RegisterAPIView(APIView):
    throttle_scope = 'register'

    def post(self, request):
        # the SAME form as the HTML page - identical validation rules
        # (password strength, unique username) on both doors
        form = CreateUserForm(request.data)
        if not form.is_valid():
            return Response({'errors': form.errors.get_json_data()},
                            status=status.HTTP_400_BAD_REQUEST)
        user = form.save()
        user.is_active = False
        user.save()
        try:
            send_verification_email(request, user)
        except OSError:
            # same recovery as the HTML view: free the username again
            user.delete()
            return Response(
                {'error': 'We could not send the verification email. '
                          'Please try again in a few minutes.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(user_payload(user), status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name='dispatch')
class VerifyEmailAPIView(APIView):
    throttle_scope = 'verify-email'

    def post(self, request):
        try:
            uid = force_str(urlsafe_base64_decode(request.data.get('uid', '')))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            # malformed uid or no such user - same as a bad token
            user = None
        if user and account_activation_token.check_token(
                user, request.data.get('token', '')):
            user.is_active = True
            user.save()
            return Response({'detail': 'Email verified - you can now log in'})
        return Response({'error': 'Invalid or expired verification link'},
                        status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_protect, name='dispatch')
class LoginAPIView(APIView):
    throttle_scope = 'login'

    def post(self, request):
        user = authenticate(request,
                            username=request.data.get('username'),
                            password=request.data.get('password'))
        if user is None:
            # one vague message on purpose: never tell an attacker which
            # of username/password was wrong, or whether the account exists
            return Response(
                {'error': 'Invalid credentials, or your email is not verified yet'},
                status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response(user_payload(user))


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Logged out'})


class MeAPIView(APIView):
    """GET /api/auth/me/ - the frontend's am-I-logged-in check on page load."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user))
