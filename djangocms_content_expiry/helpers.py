from django.contrib.auth import get_user_model


def get_authors():
    """
    Helper to return all authors created by content expiry
    """
    User = get_user_model()
    return User.objects.filter(contentexpiry__created_by__isnull=False).distinct()
