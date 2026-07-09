from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # creating the unique token
        user_id = str(user.pk)
        ts = str(timestamp)
        is_active = str(user.is_active)
        return f"{user_id}{ts}{is_active}"
    
account_activation_token = EmailVerificationTokenGenerator()

