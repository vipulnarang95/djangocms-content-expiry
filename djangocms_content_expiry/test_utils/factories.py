from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

import factory
from factory.fuzzy import FuzzyText

from djangocms_content_expiry.models import ContentExpiry


class UserFactory(factory.django.DjangoModelFactory):
    username = FuzzyText(length=12)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda u: "%s.%s@example.com" % (u.first_name.lower(), u.last_name.lower())
    )

    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = cls._get_manager(model_class)
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create_user(*args, **kwargs)


class AbstractVersionFactory(factory.django.DjangoModelFactory):
    object_id = factory.SelfAttribute("content.id")
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content)
    )
    created_by = factory.SubFactory(UserFactory)

    class Meta:
        exclude = ["content"]
        abstract = True


class ContentExpiryFactory(factory.django.DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    version = None
    expires = factory.Faker('date_object')

    class Meta:
        model = ContentExpiry
