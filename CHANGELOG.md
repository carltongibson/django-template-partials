# CHANGELOG

* Deprecated passing arguments to the `inline` argument of the `partialdef`
  tag. Either use `inline` or nothing.

## 24.4 (2024-08-16)

* Fixed a regression in 24.3 for inline partials with wrapping content.

## 24.3 (2024-08-16)

* Added official Django 5.1 support.

* Allowed adding the partial name to the `endpartialdef` tag, similar to how
  `endblock` allows specifying the block name again.

  Thanks to Matthias Kestenholz

## 24.2 (2024-04-08)

* Implemented ``reset()`` on the partial loader to pass down to child loaders
  when the autoreloader detects a template change. This allows the cached loader
  to be correctly cleared in development.

  (The underlying issue here was masked prior to v24.1.)

## 24.1 (2024-04-04)

* Fixed a bug in how the partial loader called down to the cached loader when
  present.

  Thanks to Marco Garbelini.

## 23.4 (2023-11-20)

* Fixed a bug automatically wrapping the template loaders when another installed
  app had already instantiated the template engine.

  Thanks to Jannis Vajen.

## 23.3 (2023-10-08)

This is the first major update since the initial release. It includes a number
of bug fixes and adjustments from the feedback received.

Thanks to everyone who has tried the package and provided feedback.

Please read these notes carefully if you are upgrading from a previous version.

* The partial definition block tags have been renamed to `partialdef` and `endpartialdef`
(from `startpartial` and `endpartial`) to better correspond to Django's naming
conventions. (All the built-in tags follow the `<name>` `end<name>` pattern.)

  The old tag names are deprecated. A global search/replace for
  `startpartial`/`partialdef` and `endpartial`/`endpartialdef` should be
  sufficient to upgrade.

  Thanks to Justin Muncaster and Christian Tanul.

* The opening `partialdef` tag now accepts an optional `inline` argument, that enables
  you to output the partial at the same time as defining it for later use.

        {% partialdef my-great-partial inline=True %}
            ...
        {% endpartialdef %}

  This smooths initially wrapping an existing part of your page, as well as keeping the
  content *inline*, if that suits your case better.

  Thanks to George Hickman.

  Note: Passing `inline=True` has been deprecated in 24.5. Only pass `inline` instead.

* Adding `"template_partials"` to `INSTALLED_APPS` will now **automatically** configure
  the partials template loader.

  This means that you can remove the `TEMPLATES` `'OPTIONS'` `'loaders'` (and,
  likely, restore `APP_DIRS: True`) changes that you made when first installing
  template-partials.

  If you need more fine grained control over your template loaders, an
  alternative `AppConfig` is available that will not automatically configure
  the loader.

  Please see the [README](./README.md) for full details.

  Thanks to Vinay Sajip.

* The [README](./README.md) documentation has been expanded and improved for this release.
  Please review that again to make sure you don't miss anything.

* Thanks also in this release to Andreu Vallbona for miscellaneous small fixes.


## 23.2 (2023-06-13)

* Fixed exception when rendering the Django debug view for a template error in a partial.
  Thanks to Harro van der Klauw.

## 23.1 (2023-06-10)

* Initial release.
