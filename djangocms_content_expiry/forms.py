from django import forms
from django.contrib.admin import widgets
from django.contrib.admin.sites import site

from .models import ContentExpiry


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
