# django-template-partials

Reusable named inline partials for the Django Template Language.

## Watch the talk

This is the `django-template-partials` package I discussed in my DjangoCon Europe 2023
talk in Edinburgh.

For a quick introduction, you can watch the video on YouTube. 🍿

[![DjangoCon Europe 2023 | Yak-shaving to Where the Puck is Going to Be.](https://img.youtube.com/vi/_3oGI4RC52s/0.jpg)](https://www.youtube.com/watch?v=_3oGI4RC52s)

## Installation

Install with pip:

```bash
pip install django-template-partials
```

Then set up your project, as per this example:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
               ...,
            ],
            "builtins": [
                # If you want to avoid doing {% load partials %} in your templates
                "template_partials.templatetags.partials"
            ],
        },
    },
]
INSTALLED_APPS = [
    "template_partials",
    ...,
]
```

## Usage

Load the `partials` tags (if you haven't specified them via "builtins" as suggested above)
and define a re-usable partial at the top of your template:

```html
{% load partials %}

{% startpartial test-partial %}
TEST-PARTIAL-CONTENT
{% endpartial %}
```

Then later you can reuse it:

```
{% block main %}
BEGINNING
{% partial test-partial %}
MIDDLE
{% partial test-partial %}
END
{% endblock main %}
```

`django-template-partials` is also integrated with the template loader, so you can pass a template
plus a partial name to the loader to have just that part rendered:

```python
self.template_name = "example.html#test-partial"
```

The rest of your view logic remains the same.

## Automatic configuration of template loader integration

By default, if you just add `"template_partials"` to your `INSTALLED_APPS`, a template loader which
can handle partials will be automatically configured for any template engine with a backend of
`"django.template.backends.django.DjangoTemplates"`.

If you want to avoid this autoconfiguration, set up your `INSTALLED_APPS` like this:

```python
INSTALLED_APPS = [
    "template_partials.apps.SimpleAppConfig",
    ...,
]
```
If you do this, you will need to configure the template loader yourself. For this, a `wrap_loaders()` function is
provided, and it can be used to configure any specific template engine instance with a loader that handles partials.
For example, you can use the [`NAME`](https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-TEMPLATES-NAME)
key:

```python
from template_partials.apps import wrap_loaders

TEMPLATES = [
    ...,
    {
        "BACKEND": "...",
        "NAME": "myname",
        "OPTIONS": {
           ...,
        },
    },
    ...,
]

wrap_loaders("myname")
```
Note that if `NAME` isn't provided, the penultimate element of the `BACKEND` value is used - for example,
`"django.template.backends.django.DjangoTemplates"` would be equivalent to a `NAME` of `"django"`.

What `wrap_loaders` does is something like this:

```python
from django.conf import settings

default_loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]
partial_loaders = [("template_partials.loader.Loader", cached_loaders)]

settings.TEMPLATES[...]['OPTIONS']['loaders'] = partial_loaders
```

where `TEMPLATES[...]` is the entry in `TEMPLATES` with the `NAME` matching what's passed to `wrap_loaders()`.

## Documentation

Fuller docs and write up still ***COMING SOON***, but the talk explains most of
it.

Enjoy! 🚀

## Running the tests

Fork, then clone the repo:

```sh
git clone git@github.com:your-username/django-template-partials.git
```

Set up a venv:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .[tests]
```

Then you can run the tests with the `just` command runner:

```sh
just test
```

Or with coverage:

```sh
just coverage
```

If you don't have `just` installed, you can look in the `justfile` for a commands that are run.
