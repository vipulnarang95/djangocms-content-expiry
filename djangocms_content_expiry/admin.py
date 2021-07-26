from django.contrib import admin

from .models import ContentExpiryContent


@admin.register(ContentExpiryContent)
class ContentExpiryAdmin(admin.ModelAdmin):
    pass
