*************************
django CMS Content Expiry
*************************

============
Installation
============

Requirements
============

django CMS Content Expiry requires that you have a django CMS 4.0 (or higher) project already running and set up.


To install
==========

Add ``djangocms_content_expiry`` to your project's ``INSTALLED_APPS``.

Run::

    python manage.py migrate djangocms_content_expiry

to perform the application's database migrations.


Configuration
=============

Default expiry dates for new versions using DefaultContentExpiryConfiguration
-----------------------------------------------------------------------------
The model ``DefaultContentExpiryConfiguration`` allows you to create a default in months for each content type. When a new version is created of a specific content type, this value is used. If a value cannot be foudn for a content type, the value of the setting :ref:`CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_DURATION` is used.


Limit a Content Type values list in the Content expiry Changelist
-----------------------------------------------------------------
The Content Expiry changelist can limit the queryet based on third party requirements. It is currently used by the CMS PageContents model to filter out and show only the pages for the current site. The feature can be used to limit the queryset in anyway that a third party package requires.


.. code-block:: python

    # some_app/cms_config.py
    from cms.app_base import CMSAppConfig


    def some_queryset_modifier(queryset, request):
        queryset.filter(version__some_model="something")
        return queryset


     class SomeConfig(CMSAppConfig):
        djangocms_content_expiry_changelist_queryset_filters=[
            some_queryset_modifier,
        ]


Setting: CMS_CONTENT_EXPIRY_DEFAULT_RANGEFILTER_DELTA
-----------------------------------------------------
The default Content Expiry changelist is filtered by a date range which is 30 days by default. This can be changed by setting a value in days as an integer in settings.py::

    CMS_CONTENT_EXPIRY_DEFAULT_RANGEFILTER_DELTA=30


Setting: CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_DURATION
-----------------------------------------------------------
The default Content Expiry creation expiry date defaults to 12 months. This is the date that is used if a value is not set for the content type in the model :ref:`DefaultContentExpiryConfiguration`.

    CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_DURATION=12


Setting: CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT
---------------------------------------------------------------------
The default string format that should be exported for the expiry date in the csv file export. Uses formats suitable for python datetime strftime. The default is set as: "%Y/%m/%d %H:%M %z"

    CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_EXPORT_DATE_FORMAT


Setting: CMS_DEFAULT_CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_EXPIRY
---------------------------------------------------------------------------------
The default cache timeout period in seconds for the PageContent exclusion list used to display only the current sites PageContents shown in the Content Expiry changelist.
The default is set to 300 seconds, after this time the cache has expired.

    CMS_DEFAULT_CONTENT_EXPIRY_CHANGELIST_PAGECONTENT_EXCLUSION_CACHE_EXPIRY


Commands
=============

create_existing_versions_expiry_records
---------------------------------------
When installing the package into an existing project that already has versions, you may want to populate the existing versions with a content expiry record.

If content types have a different default value than set in the setting: :ref:`CMS_CONTENT_EXPIRY_DEFAULT_CONTENT_EXPIRY_DURATION`, you will need to create entries in the model :ref:`DefaultContentExpiryConfiguration`

Run::

    python manage.py create_existing_versions_expiry_records

Testing
=======

To run all the tests the only thing you need to do is run

    pip install -r tests/requirements.txt
    python setup.py test
