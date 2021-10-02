from django import forms
from django.contrib.admin import widgets
from django.contrib.admin.sites import site

from .models import ContentExpiry, DefaultContentExpiryConfiguration


class ForeignKeyReadOnlyWidget(widgets.ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in a read only interface rather than
    in a <select> box.
    """
    template_name = 'admin/widgets/foreign_key_read_only.html'


class ContentExpiryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        version_field = ContentExpiry._meta.get_field('version').remote_field
        self.fields['version'].widget = ForeignKeyReadOnlyWidget(version_field, site)

        user_field = ContentExpiry._meta.get_field('created_by').remote_field
        self.fields['created_by'].widget = ForeignKeyReadOnlyWidget(user_field, site)


class DefaultContentExpiryConfigurationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_key_ctype = 'content_type'

        # If adding
        if not getattr(self.instance, 'pk', None):
            # Only get items that haven't been set yet
            self.fields[field_key_ctype].queryset = self.fields[field_key_ctype].queryset.filter(
                defaultcontentexpiryconfiguration__isnull=True
            )
        # Otherwise, changing (viewing / editing)
        else:
            content_type_field = DefaultContentExpiryConfiguration._meta.get_field(field_key_ctype).remote_field
            self.fields[field_key_ctype].widget = ForeignKeyReadOnlyWidget(content_type_field, site)

    class Meta:
        model = DefaultContentExpiryConfiguration
        exclude = []
