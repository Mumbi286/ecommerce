from django.contrib.auth.models import User
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse


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
