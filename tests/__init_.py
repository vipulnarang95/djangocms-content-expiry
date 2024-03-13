import django

from packaging.version import Version

DJANGO_4_2 = Version(django.get_version()) >= Version('4.2')

if not DJANGO_4_2:
    from cms.test_utils.testcases import CMSTestCase
    CMSTestCase.assertQuerySetEqual = CMSTestCase.assertQuerysetEqual
