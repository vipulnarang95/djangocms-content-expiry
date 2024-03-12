from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import re_path, reverse

from djangocms_moderation import admin as moderation_admin
from djangocms_moderation.models import ModerationCollection, ModerationRequest
from djangocms_versioning import admin

from djangocms_content_expiry.constants import CONTENT_EXPIRY_COMPLIANCE_FIELD_LABEL
from djangocms_content_expiry.models import ContentExpiry


def _get_expiry_link(self, obj, request):
    """
    Generate a content expiry link for the Versioning Admin
    """
    expiry_url = reverse(
        "admin:{app}_{model}_change".format(
            app=ContentExpiry._meta.app_label, model=ContentExpiry._meta.model_name
        ),
        args=(obj.contentexpiry.pk,),
    )
    return render_to_string(
        'djangocms_content_expiry/admin/icons/additional_content_settings_icon.html',
        {
            "url": f"{expiry_url}?_to_field=id&_popup=1",
            "field_id": f"contentexpiry_{obj.pk}",
        }
    )


admin.VersionAdmin._get_expiry_link = _get_expiry_link


def get_state_actions(func):
    """
    Add additional content settings action to Versioning state actions
    """
    def inner(self, *args, **kwargs):
        state_list = func(self, *args, **kwargs)
        state_list.append(self._get_expiry_link)
        return state_list
    return inner


admin.VersionAdmin.get_state_actions = get_state_actions(admin.VersionAdmin.get_state_actions)


def compliance_number(self, obj):
    version = ContentExpiry.objects.filter(version=obj.pk)
    if version:
        return version[0].compliance_number
    return ""


compliance_number.short_description = CONTENT_EXPIRY_COMPLIANCE_FIELD_LABEL
admin.VersionAdmin.compliance_number = compliance_number


def get_list_display(func):
    """
    Register the compliance number field with the Versioning Admin
    """
    def inner(self, request):
        list_display = func(self, request)
        created_by_index = list_display.index('created_by')
        return list_display[:created_by_index] + ('compliance_number',) + list_display[created_by_index:]

    return inner


admin.VersionAdmin.get_list_display = get_list_display(admin.VersionAdmin.get_list_display)


def _get_urls(func):
    """
    Add custom Version Lock urls to Versioning urls
    """
    def inner(self, *args, **kwargs):
        url_list = func(self, *args, **kwargs)
        info = self.model._meta.app_label, self.model._meta.model_name
        url_list.insert(0, re_path(
            r'^copy/',
            self.admin_site.admin_view(self.copy_content_expiry_view),
            name="{}_{}_copy".format(*info),
        ))
        return url_list
    return inner


moderation_admin.ModerationRequestTreeAdmin.get_urls = _get_urls(moderation_admin.ModerationRequestTreeAdmin.get_urls)


def copy_content_expiry_view(self, request):
    """
    Copy expiration date and compliance number to all items in a collection
    :param request:
    :return: Redirect to the moderation changelist to ensure a page reload occurs
    """
    compliance_copy = request.GET.get("copy", None)
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
                    if compliance_copy == "compliance":
                        mr_content_expiry = mr_version.contentexpiry
                        mr_content_expiry.compliance_number = content_expiry.compliance_number
                        mr_content_expiry.save()
                    else:
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
