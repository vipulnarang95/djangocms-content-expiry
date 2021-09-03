from setuptools import find_packages, setup

import djangocms_content_expiry


INSTALL_REQUIREMENTS = [
    "Django>=1.11,<3.0",
    "django-cms",
    "django-admin-rangefilter",
]


setup(
    name="djangocms-content-expiry",
    packages=find_packages(),
    include_package_data=True,
    version=djangocms_content_expiry.__version__,
    description=djangocms_content_expiry.__doc__,
    long_description=open("README.rst").read(),
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
    install_requires=INSTALL_REQUIREMENTS,
    author="Eliga Services",
    test_suite="test_settings.run",
    author_email="enquiries@eliga.services",
    url="https://github.com/EligaServices/djangocms-content-expiry",
    license="BSD",
    zip_safe=False,
)
