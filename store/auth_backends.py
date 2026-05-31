from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailAuthBackend(ModelBackend):
    """
    Allow staff/admin users to log in with their email address
    in addition to the default username-based login.
    Customer-facing login already uses username; this backend
    supplements it for sub-admins created through User Management.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Pick the first active staff user if duplicates exist
            user = User.objects.filter(email__iexact=username, is_active=True).first()
            if user is None:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
