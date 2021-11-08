from django.db import models
from django.urls import reverse

from polymorphic.models import PolymorphicModel


class ProjectGrouper(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class ProjectContent(PolymorphicModel):
    grouper = models.ForeignKey(ProjectGrouper, on_delete=models.CASCADE)
    topic = models.CharField(max_length=20)

    def __str__(self):
        return self.topic

    def get_absolute_url(self):
        return reverse("admin:polymorphic_project_projectcontent_changelist")

    class Meta:
        # Important for djangocms-versioning support, without this the GenericForeignKey
        # on the Version will yield None for the "content"
        base_manager_name = '_original_manager'


class ArtProjectContent(ProjectContent):
    artist = models.CharField(max_length=20)

    def __str__(self):
        return self.artist

    def get_absolute_url(self):
        return reverse("admin:polymorphic_project_artprojectcontent_changelist")

    class Meta:
        # Important for djangocms-versioning support, without this the GenericForeignKey
        # on the Version will yield None for the "content"
        base_manager_name = '_original_manager'


class ResearchProjectContent(ProjectContent):
    supervisor = models.CharField(max_length=20)

    def __str__(self):
        return self.supervisor

    def get_absolute_url(self):
        return reverse("admin:polymorphic_project_researchprojectcontent_changelist")

    class Meta:
        # Important for djangocms-versioning support, without this the GenericForeignKey
        # on the Version will yield None for the "content"
        base_manager_name = '_original_manager'
