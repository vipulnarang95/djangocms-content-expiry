from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

import factory
from djangocms_moderation.models import (
    ModerationCollection,
    ModerationRequest,
    ModerationRequestTreeNode,
    Workflow,
)
from factory.fuzzy import FuzzyInteger, FuzzyText

from djangocms_content_expiry.models import (
    ContentExpiry,
    DefaultContentExpiryConfiguration,
)


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


class WorkflowFactory(factory.django.DjangoModelFactory):
    name = FuzzyText(length=12)

    class Meta:
        model = Workflow


class ModerationCollectionFactory(factory.django.DjangoModelFactory):
    name = FuzzyText(length=12)
    author = factory.SubFactory(UserFactory)
    workflow = factory.SubFactory(WorkflowFactory)

    class Meta:
        model = ModerationCollection


class ModerationRequestFactory(factory.django.DjangoModelFactory):
    collection = factory.SubFactory(ModerationCollectionFactory)
    version = None
    language = 'en'
    author = factory.LazyAttribute(lambda o: o.collection.author)

    class Meta:
        model = ModerationRequest


class RootModerationRequestTreeNodeFactory(factory.django.DjangoModelFactory):
    moderation_request = factory.SubFactory(ModerationRequestFactory)

    class Meta:
        model = ModerationRequestTreeNode

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Make sure this is the root of a tree"""
        return model_class.add_root(*args, **kwargs)


class ChildModerationRequestTreeNodeFactory(factory.django.DjangoModelFactory):
    moderation_request = factory.SubFactory(ModerationRequestFactory)
    parent = factory.SubFactory(RootModerationRequestTreeNodeFactory)

    class Meta:
        model = ModerationRequestTreeNode
        inline_args = ("parent",)

    @classmethod
    def _create(cls, model_class, parent, *args, **kwargs):
        """Make sure this is the child of a parent node"""
        return parent.add_child(*args, **kwargs)


class DefaultContentExpiryConfigurationFactory(factory.django.DjangoModelFactory):
    content_type = None
    duration = FuzzyInteger(1, 12)

    class Meta:
        model = DefaultContentExpiryConfiguration
