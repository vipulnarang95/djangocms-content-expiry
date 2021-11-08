from django.contrib.contenttypes.models import ContentType

import factory
from djangocms_versioning.models import Version
from djangocms_versioning.signals import post_version_operation, pre_version_operation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from djangocms_content_expiry.models import ContentExpiry
from djangocms_content_expiry.test_utils.factories import (
    AbstractVersionFactory,
    UserFactory,
)

from .models import (
    ArtProjectContent,
    ProjectContent,
    ProjectGrouper,
    ResearchProjectContent,
)


class AbstractProjectContentVersionFactory(AbstractVersionFactory):
    class Meta:
        exclude = ["content"]
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        We have to ensure that the Version object takes the root Polymorphic model
        and not the concrete model or else the mapping breaks.
        """
        obj = model_class(*args, **kwargs)
        # Make sure Version.content_type uses ProjectContent
        obj.content_type = ContentType.objects.get_for_model(ProjectContent)
        obj.save()
        return obj


# Project models
class ProjectGrouperFactory(DjangoModelFactory):
    name = FuzzyText(length=10)

    class Meta:
        model = ProjectGrouper


class ProjectContentFactory(DjangoModelFactory):
    grouper = factory.SubFactory(ProjectGrouperFactory)
    topic = FuzzyText(length=20)

    class Meta:
        model = ProjectContent


class ProjectContentVersionFactory(AbstractProjectContentVersionFactory):
    content = factory.SubFactory(ProjectContentFactory)

    class Meta:
        model = Version


@factory.django.mute_signals(pre_version_operation, post_version_operation)
class ProjectContentExpiryFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    version = factory.SubFactory(ProjectContentVersionFactory)
    expires = factory.Faker('date_object')

    class Meta:
        model = ContentExpiry


# Art Project models
class ArtProjectContentFactory(DjangoModelFactory):
    grouper = factory.SubFactory(ProjectGrouperFactory)
    artist = FuzzyText(length=20)

    class Meta:
        model = ArtProjectContent


class VersionWithArtProjectContentFactory(AbstractProjectContentVersionFactory):
    content = factory.SubFactory(ArtProjectContentFactory)

    class Meta:
        model = Version


@factory.django.mute_signals(pre_version_operation, post_version_operation)
class ArtProjectContentExpiryFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    version = factory.SubFactory(VersionWithArtProjectContentFactory)
    expires = factory.Faker('date_object')

    class Meta:
        model = ContentExpiry


# Research Project models
class ResearchProjectContentFactory(DjangoModelFactory):
    grouper = factory.SubFactory(ProjectGrouperFactory)
    supervisor = FuzzyText(length=20)

    class Meta:
        model = ResearchProjectContent


class VersionWithResearchProjectContentFactory(AbstractProjectContentVersionFactory):
    content = factory.SubFactory(ResearchProjectContentFactory)

    class Meta:
        model = Version


@factory.django.mute_signals(pre_version_operation, post_version_operation)
class ResearchProjectContentExpiryFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    version = factory.SubFactory(VersionWithResearchProjectContentFactory)
    expires = factory.Faker('date_object')

    class Meta:
        model = ContentExpiry
