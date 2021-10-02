from django.conf.urls import url
from django.shortcuts import redirect
from django.urls import reverse

from djangocms_moderation import admin as moderation_admin
from djangocms_moderation.models import ModerationCollection, ModerationRequest
from djangocms_versioning import admin

from djangocms_content_expiry.constants import CONTENT_EXPIRY_EXPIRE_FIELD_LABEL
from djangocms_content_expiry.models import ContentExpiry


def expires(self, obj):
    version = ContentExpiry.objects.filter(version=obj.pk)
    if version:
        return version[0].expires
    return ""


expires.short_description = CONTENT_EXPIRY_EXPIRE_FIELD_LABEL
admin.VersionAdmin.expire = expires


def get_list_display(func):
    """
    Register the expires field with the Versioning Admin
    """
    def inner(self, request):
        list_display = func(self, request)
        created_by_index = list_display.index('created_by')
        return list_display[:created_by_index] + ('expire',) + list_display[created_by_index:]

    return inner


admin.VersionAdmin.get_list_display = get_list_display(admin.VersionAdmin.get_list_display)


def _get_urls(func):
    """
    Add custom Version Lock urls to Versioning urls
    """
    def inner(self, *args, **kwargs):
        url_list = func(self, *args, **kwargs)
        info = self.model._meta.app_label, self.model._meta.model_name
        url_list.insert(0, url(
            r'^copy/',
            self.admin_site.admin_view(self.copy_content_expiry_view),
            name="{}_{}_copy".format(*info),
        ))
        return url_list
    return inner


moderation_admin.ModerationRequestTreeAdmin.get_urls = _get_urls(moderation_admin.ModerationRequestTreeAdmin.get_urls)


def copy_content_expiry_view(self, request):
    collection_id = request.GET.getlist("collection__id")
    collection_id = int(collection_id[0])
    moderation_request_id = request.GET.getlist("moderation_request__id")
    moderation_request_id = int(moderation_request_id[0])

    if collection_id and moderation_request_id:
        collection = ModerationCollection.objects.get(id=collection_id)
        moderation_request = ModerationRequest.objects.get(id=moderation_request_id)
        version = moderation_request.version

        redirect_url = reverse('admin:djangocms_moderation_moderationrequesttreenode_changelist')
        redirect_url = "{}?moderation_request__collection__id={}".format(
            redirect_url,
            collection_id
        )

        if hasattr(version, "contentexpiry"):
            content_expiry = version.contentexpiry

            for mr in collection.moderation_requests.all():
                mr_version = mr.version
                if hasattr(mr_version, "contentexpiry"):
                    mr_content_expiry = mr_version.contentexpiry
                    mr_content_expiry.expires = content_expiry.expires
                    mr_content_expiry.save()
                else:
                    ContentExpiry.objects.create(
                        created_by=request.user,
                        version=mr_version,
                        expires=content_expiry.expires,
                    )

        return redirect(redirect_url)


moderation_admin.ModerationRequestTreeAdmin.copy_content_expiry_view = copy_content_expiry_view
