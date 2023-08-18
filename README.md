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

Then set up your project:

```python
# Install app and configure loader.
default_loaders = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]
partial_loaders = [("template_partials.loader.Loader", cached_loaders)]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        # Comment this out when manually defining loaders.
        # "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": True,
            # TODO: Add wrap_loaded function to the called from an AppConfig.ready().
            "loaders": partial_loaders,
        },
    },
]
INSTALLED_APPS = [
    "template_partials",
    ...,
]
```

## Usage

Load the `partials` tags and define a re-usable partial at the top of your
template:

```html
{% load partials %}


{% startpartial table-row %}
<tr>
    <td>{{ product.name }}</td>
</tr>
{% endpartial %}


{% startpartial table-rows %}
    {% for product in products %}
        {% partial table-row %}
    {% endfor %}
{% endpartial %}
```

Then later you can reuse it:

```
{% block main %}
<table>
    <tbody>
    {% partial table-rows %}
    </tbody>
</table>
{% endblock main %}
```

`django-template-partials` is also integrated with the template loader, so you can pass a template plus a partial name to the loader to have just that part rendered:

```python
self.template_name = "example.html#test-partial"
```

The rest of your view logic remains the same.

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
