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

Run::

# TODO

Add ``djangocms_content_expiry`` to your project's ``INSTALLED_APPS``.

Run::

    python manage.py migrate djangocms_content_expiry

to perform the application's database migrations.



Configuration
=============

The default Content Expiry changelist is filtered by a date range which is 30 days by default. This can be changed by setting a value in days as an integer in settings.py::

    CMS_CONTENT_EXPIRY_DEFAULT_RANGEFILTER_DELTA=60


Testing
=======

To run all the tests the only thing you need to do is run

    pip install -r tests/requirements.txt
    python setup.py test
