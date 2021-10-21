from aldryn_client import forms


class Form(forms.BaseForm):
    def to_settings(self, data, settings):
        settings['INSTALLED_APPS'].extend([
            'rangefilter',
        ])
        settings["DJANGOCMS_CONTENT_EXPIRY_ENABLED"] = True
        return settings
