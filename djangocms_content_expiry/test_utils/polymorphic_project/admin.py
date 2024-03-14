from django.contrib import admin
from django.urls import path

from .models import (
    ArtProjectContent,
    ProjectContent,
    ProjectGrouper,
    ResearchProjectContent,
)
from .views import PreviewView


class VersionedContentAdmin(admin.ModelAdmin):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "<int:id>/preview/",
                self.admin_site.admin_view(PreviewView.as_view()),
                name="{}_{}_preview".format(*info),
            )
        ] + super().get_urls()


@admin.register(ProjectGrouper)
class ProjectGrouperAdmin(admin.ModelAdmin):
    pass


@admin.register(ProjectContent)
class ProjectContentAdmin(VersionedContentAdmin):
    pass


@admin.register(ArtProjectContent)
class ArtProjectContentAdmin(VersionedContentAdmin):
    pass


@admin.register(ResearchProjectContent)
class ResearchProjectContentAdmin(VersionedContentAdmin):
    pass
