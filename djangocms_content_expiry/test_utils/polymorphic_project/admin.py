from django.contrib import admin

from .models import (
    ArtProjectContent,
    ProjectContent,
    ProjectGrouper,
    ResearchProjectContent,
)


@admin.register(ArtProjectContent)
class ArtProjectContentAdmin(admin.ModelAdmin):
    pass


@admin.register(ProjectGrouper)
class ProjectGrouperAdmin(admin.ModelAdmin):
    pass


@admin.register(ProjectContent)
class ProjectContentAdmin(admin.ModelAdmin):
    pass


@admin.register(ResearchProjectContent)
class ResearchProjectContentAdmin(admin.ModelAdmin):
    pass
