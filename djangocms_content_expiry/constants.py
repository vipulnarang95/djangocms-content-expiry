from django.utils.translation import gettext_lazy as _


CONTENT_EXPIRY_EXPIRE_FIELD_LABEL = _("expiry date")
CONTENT_EXPIRY_COMPLIANCE_FIELD_LABEL = _("compliance number")

CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_KEY = "djangocms_content_expiry_changelist_pagecontent_exclusion"
CONTENT_EXPIRY_FIELDSETS = ['compliance_number', 'created_by', 'version', 'expires']
