from django.utils import timezone

import factory
from djangocms_versioning.models import Version
from djangocms_versioning.signals import post_version_operation, pre_version_operation
from factory.fuzzy import FuzzyChoice, FuzzyText

from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.test_utils.factories import (
    AbstractVersionFactory,
    UserFactory,
)

from .models import Poll, PollContent


class PollFactory(factory.django.DjangoModelFactory):
    name = FuzzyText(length=6)

    class Meta:
        model = Poll


class PollContentFactory(factory.django.DjangoModelFactory):
    poll = factory.SubFactory(PollFactory)
    language = FuzzyChoice(["en", "fr", "it"])
    text = FuzzyText(length=24)

    class Meta:
        model = PollContent


class PollVersionFactory(AbstractVersionFactory):
    content = factory.SubFactory(PollContentFactory)

    class Meta:
        model = Version


class PollContentWithVersionFactory(PollContentFactory):
    @factory.post_generation
    def version(self, create, extracted, **kwargs):
        # NOTE: Use this method as below to define version attributes:
        # PollContentWithVersionFactory(version__label='label1')
        if not create:
            # Simple build, do nothing.
            return
        PollVersionFactory(content=self, **kwargs)


@factory.django.mute_signals(pre_version_operation, post_version_operation)
class PollContentExpiryFactory(factory.django.DjangoModelFactory):
    compliance_number = FuzzyText(length=15)
    created_by = factory.SubFactory(UserFactory)
    version = factory.SubFactory(PollVersionFactory)
    expires = factory.Faker('date_time', tzinfo=timezone.get_current_timezone())

    class Meta:
        model = ContentExpiry
