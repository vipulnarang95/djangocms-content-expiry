=========
Changelog
=========

unreleased
==========
* fix: Content Expiry Changelist: Removed polymorphic model support due to persistant timeouts and low performance

0.0.5 (2021-11-16)
==================
* fix: Content Expiry Changelist: Timeouts due to Content Type filtering by polymorphic models using the full data set.

0.0.4 (2021-11-08)
==================
* feat: Content Expiry Changelist Content Type filter: Handle filtering by polymorphic models such as filer image / file.

0.0.3 (2021-11-05)
==================
* feat: Filter the Content Expiry Changelist PageContents and Alias Content Type by site, the feature can also be used by other third party packages to restrict the entries shown in the changelist.

0.0.2 (2021-11-01)
==================
* fix: Provide content links in the Content Expiry changelist and csv file export
* fix: Content Expiry changelist filter dates should be for the future not the past
* fix: CSV export Dates are not formatting correctly in Excel
* fix: CSV export external urls used for for the url column

0.0.1 (2021-10-04)
==================

* Initial release
