from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.mail.backends.base import BaseEmailBackend
from django.test import Client, TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .token import account_activation_token


class FailingEmailBackend(BaseEmailBackend):
    """A fake email backend that behaves like Gmail being unreachable."""
    def send_messages(self, email_messages):
        raise OSError("SMTP server is down")


class RegistrationEmailTests(TestCase):
    def valid_form_data(self):
        return {
            'username': 'wanjiku',
            'email': 'wanjiku@example.com',
            'password1': 'a-strong-pass-123',
            'password2': 'a-strong-pass-123',
        }

    def test_registration_creates_inactive_user_and_sends_email(self):
        response = self.client.post(reverse('register'), self.valid_form_data())
        self.assertRedirects(response, reverse('email-verification-sent'))
        user = User.objects.get(username='wanjiku')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND='users.tests.FailingEmailBackend')
    def test_registration_survives_email_failure(self):
        response = self.client.post(reverse('register'), self.valid_form_data())
        # no crash - the form page is shown again with an error message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'could not send the verification email')
        # and the half-created account was rolled back
        self.assertFalse(User.objects.filter(username='wanjiku').exists())


class EmailVerificationTests(TestCase):
    def make_inactive_user(self):
        return User.objects.create_user(
            username='wanjiku', email='wanjiku@example.com',
            password='a-strong-pass-123', is_active=False,
        )

    def test_valid_link_activates_the_account(self):
        user = self.make_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        response = self.client.get(reverse('email-verification', args=[uid, token]))
        self.assertRedirects(response, reverse('email-verification-success'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_garbage_uidb64_shows_failed_page_instead_of_crashing(self):
        response = self.client.get(reverse('email-verification', args=['not-base64!!', 'sometoken']))
        self.assertRedirects(response, reverse('email-verification-failed'))

    def test_nonexistent_user_id_shows_failed_page(self):
        uid = urlsafe_base64_encode(force_bytes(999))
        response = self.client.get(reverse('email-verification', args=[uid, 'sometoken']))
        self.assertRedirects(response, reverse('email-verification-failed'))

    def test_link_stops_working_after_activation(self):
        user = self.make_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        self.client.get(reverse('email-verification', args=[uid, token]))   # first click activates
        response = self.client.get(reverse('email-verification', args=[uid, token]))  # second click
        self.assertRedirects(response, reverse('email-verification-failed'))


class ProfileTests(TestCase):
    def setUp(self):
        User.objects.create_user('wanjiku', 'wanjiku@example.com', 'a-strong-pass-123')
        self.client.login(username='wanjiku', password='a-strong-pass-123')

    def test_invalid_update_shows_the_error(self):
        response = self.client.post(reverse('profile'), {'username': '', 'email': 'w@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

    def test_valid_update_changes_the_username(self):
        response = self.client.post(reverse('profile'), {'username': 'wanjiku2', 'email': 'w@example.com'})
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(User.objects.filter(username='wanjiku2').exists())


class AuthAPITests(TestCase):
    def register_data(self, **overrides):
        data = {
            'username': 'wanjiku',
            'email': 'wanjiku@example.com',
            'password1': 'a-strong-pass-123',
            'password2': 'a-strong-pass-123',
        }
        data.update(overrides)
        return data

    def make_active_user(self):
        return User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123')

    def test_register_creates_inactive_user_and_sends_email(self):
        response = self.client.post('/api/auth/register/', self.register_data())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['username'], 'wanjiku')
        self.assertFalse(User.objects.get(username='wanjiku').is_active)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_returns_field_errors_as_json(self):
        response = self.client.post('/api/auth/register/',
                                    self.register_data(password2='does-not-match'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('password2', response.json()['errors'])

    @override_settings(EMAIL_BACKEND='users.tests.FailingEmailBackend')
    def test_register_survives_smtp_failure(self):
        response = self.client.post('/api/auth/register/', self.register_data())
        self.assertEqual(response.status_code, 503)
        # the half-created account was rolled back
        self.assertFalse(User.objects.filter(username='wanjiku').exists())

    def test_verify_email_activates_the_account(self):
        user = User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123', is_active=False)
        response = self.client.post('/api/auth/verify-email/', {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user)})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_verify_email_with_a_bad_token_is_refused(self):
        user = User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123', is_active=False)
        response = self.client.post('/api/auth/verify-email/', {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': 'garbage-token'})
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_login_is_refused_before_verification(self):
        User.objects.create_user(
            'wanjiku', 'wanjiku@example.com', 'a-strong-pass-123', is_active=False)
        response = self.client.post('/api/auth/login/', {
            'username': 'wanjiku', 'password': 'a-strong-pass-123'})
        self.assertEqual(response.status_code, 400)

    def test_login_works_and_me_returns_the_user(self):
        self.make_active_user()
        response = self.client.post('/api/auth/login/', {
            'username': 'wanjiku', 'password': 'a-strong-pass-123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me/').json()['username'], 'wanjiku')

    def test_me_requires_login(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)

    def test_logout_kills_the_session(self):
        self.make_active_user()
        self.client.post('/api/auth/login/', {
            'username': 'wanjiku', 'password': 'a-strong-pass-123'})
        self.client.post('/api/auth/logout/')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)

    def test_csrf_endpoint_sets_the_cookie(self):
        response = self.client.get('/api/auth/csrf/')
        self.assertIn('csrftoken', response.cookies)

    def test_login_without_csrf_token_is_rejected(self):
        self.make_active_user()
        client = Client(enforce_csrf_checks=True)
        response = client.post('/api/auth/login/', {
            'username': 'wanjiku', 'password': 'a-strong-pass-123'})
        self.assertEqual(response.status_code, 403)


class LoginThrottleTests(TestCase):
    # throttle counters live in the cache - clear before AND after so
    # this test neither inherits nor leaks request counts
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_eleventh_rapid_login_attempt_is_throttled(self):
        for _ in range(10):
            response = self.client.post('/api/auth/login/', {
                'username': 'ghost', 'password': 'wrong'})
            self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/auth/login/', {
            'username': 'ghost', 'password': 'wrong'})
        self.assertEqual(response.status_code, 429)
        self.assertIn('error', response.json())
