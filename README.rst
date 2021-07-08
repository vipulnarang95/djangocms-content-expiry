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


=====
Usage
=====



Testing
=======

To run all the tests the only thing you need to do is run

    pip install -r tests/requirements.txt
    python setup.py test


Documentation
=============

We maintain documentation under the ``docs`` folder using rst format.

To generate the HTML documentation you will need to install ``sphinx`` (``pip install sphinx``) and ``graphviz`` (as per
your operating system's package management system). You can then generate the docs using the following command:

Run::

    cd docs/
    make html

This should generate all html files from rst documents under `docs/_build` folder, which can be browsed.

