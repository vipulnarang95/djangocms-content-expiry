# django CMS Content Expiry

## Requirements

django CMS Content Expiry requires that you have a django CMS 4.0 (or higher) project already running and set up.

## To install

Run:

TBD

Add ``djangocms_content_expiry`` to your project's ``INSTALLED_APPS``.

Run:

    python manage.py migrate djangocms_content_expiry

to perform the application's database migrations.

## Testing

To run all the tests the only thing you need to do is run

    pip install -r tests/requirements.txt
    python setup.py test

