from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .token import account_activation_token


def send_verification_email(request, user):
    """Render and send the account-activation email.
    Raises OSError on failure - the caller decides what that means."""
    current_site = get_current_site(request)
    subject = 'Verify your email to activate your account'
    message = render_to_string('users/email-verification.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    user.email_user(subject=subject, message=message)
