# django-template-partials

[![pypi](https://img.shields.io/pypi/v/django-template-partials.svg)](https://pypi.org/project/django-template-partials/)

Reusable named inline partials for the Django Template Language.

## Watch the talk

I introduced `django-template-partials` in my DjangoCon Europe 2023 talk in Edinburgh.

For a quick introduction, you can watch the video on YouTube. 🍿

[![DjangoCon Europe 2023 | Yak-shaving to Where the Puck is Going to Be.](https://img.youtube.com/vi/_3oGI4RC52s/0.jpg)](https://www.youtube.com/watch?v=_3oGI4RC52s)

## Installation

Install with pip:

```bash
pip install django-template-partials
```

Then add to `INSTALLED_APPS` and you're good go.

```python
INSTALLED_APPS = [
    "template_partials",
    ...,
]
```

See <a href="#advanced-configuration">Advanced configuration (below)</a> for
more options.

Please see the [CHANGELOG](https://github.com/carltongibson/django-template-partials/blob/main/CHANGELOG.md) if you are upgrading from a previous version.

## Basic Usage

Once installed, load the `partials` tags and define a re-usable partial at the top of your template:

```html
{% load partials %}

{% partialdef test-partial %}
TEST-PARTIAL-CONTENT
{% endpartialdef %}
```

For extra readability, you can optionally add the name to your `{% endpartialdef %}` tag. For
example:

```html
{% load partials %}

{% partialdef test-partial %}
TEST-PARTIAL-CONTENT
{% endpartialdef test-partial %}
```

### Fragment Re-use

With the partial defined, you can reuse it multiple times later:

```
{% block main %}
BEGINNING
{% partial test-partial %}
MIDDLE
{% partial test-partial %}
END
{% endblock main %}
```

The partial content will be rendered in each time the named partial is used.


### Via the template loader

`django-template-partials` is also integrated with the template loader, so you
can pass a template plus a partial name to the loader to have just that part
rendered:

```python
# In view handler…
self.template_name = "example.html#test-partial"
```

The rest of your view logic remains the same.

This means that you can also use the partial with the `include` tag:

```html+django
{% include "example.html#test-partial" %}
```

### Outputting inline

You might want to wrap an existing part of your page, and continue rendering
the content inside your partial, use the `inline` argument in that situation:

```html
{% block main %}
{% partialdef inline-partial inline %}
CONTENT
{% endpartialdef %}
{% endblock main %}
```

### Controlling the context

A template partial is rendered with the current context.

This means it works in, for example, a loop as expected:

```html+django
{% for object in object_list %}
    {% partial test-partial %}
{% endfor %}
```

If you need to adjust the context, use the `with` tag as normal:

```html+django
{% with name=value othername=othervalue %}
    {% partial test-partial %}
{% endwith %}
```

#### Capturing output

Rendering a partial — say a pagination widget — may be computationally expensive.

It's out-of-scope for `django-template-partials` to capture the generated HTML
to the context, but other options exist, such as the [Slipper's library
fragment tag](https://mitchel.me/slippers/docs/template-tags-filters/#fragment),
that allows exactly this behaviour.


### Adding partials to template builtins.

Maybe you don't want to load the partials tags in every template…

```html+django
{% load partials %}
```

The [Django Template Language's OPTIONS](https://docs.djangoproject.com/en/4.2/topics/templates/#django.template.backends.django.DjangoTemplates)
allow you to add to the `builtins` that are loaded for every template. You can
add the partials tags there:

```
OPTIONS = {
    "builtins": ["template_partials.templatetags.partials"],
}
```


That's the basics. Enjoy! 🚀


<h2 id="advanced-configuration">Advanced configuration</h2>

By default, adding `"template_partials"` to your `INSTALLED_APPS` will
configure any Django template backend to use the partials template loader.

If you need to control this behaviour, you can use an alternative
`SimpleAppConfig`, which **will not** adjust your `TEMPLATES` setting:

```python
INSTALLED_APPS = [
    "template_partials.apps.SimpleAppConfig",
    ...,
]
```

If you use `SimpleAppConfig`, you will need to configure the template loader yourself.

A `wrap_loaders()` function is available, and can be used to configure any
specific template engine instance with the template partials loader.

You can use the backend's [`NAME`](https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-TEMPLATES-NAME)
to `wrap_loaders()` to add the partial loader just for that backend:

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

If the `NAME` isn't provided, the penultimate element of the `BACKEND` value is
used - for example, `"django.template.backends.django.DjangoTemplates"` would
be equivalent to a `NAME` of `"django"`.

Under the hood, `wrap_loaders()` is equivalent to explicitly defining the
`loaders` by-hand. Assuming defaults…

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

… where `TEMPLATES[...]` is the entry in `TEMPLATES` with the `NAME` matching
that passed to `wrap_loaders()`.


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

If you don't have `just` installed, you can look in the `justfile` for a
commands that are run.
