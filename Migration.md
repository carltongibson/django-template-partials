# 🔄 Migration Guide: django-template-partials to Django Core 🎉

When Django 6.0 includes template partials functionality in core, you'll need to migrate your existing `django-template-partials` implementation. Follow these steps:

## 📋 Migration Steps

### 1. 🗑️ Remove from INSTALLED_APPS

Remove `"template_partials"` (or `"template_partials.apps.SimpleAppConfig"`) from your `INSTALLED_APPS`:

```python
# Before
INSTALLED_APPS = [
    "template_partials",  # Remove this line
    "django.contrib.admin",
    # ... other apps
]

# After
INSTALLED_APPS = [
    "django.contrib.admin",
    # ... other apps
]
```

### 2. ⚙️ Remove Manual TEMPLATES Setting Changes

If you manually configured the template loader or added partials to builtins, remove these configurations:

```python
# Remove from TEMPLATES OPTIONS if present
OPTIONS = {
    "builtins": [
        "template_partials.templatetags.partials",  # Remove this line
    ],
}

# Remove custom loader configurations if you used wrap_loaders() or manual setup
# loaders = [("template_partials.loader.Loader", cached_loaders)]  # Remove
```

### 3. 🏷️ Remove Template Tag Loading

Remove `{% load partials %}` from all your templates since partials is built-in:

```html
<!-- Before -->
{% load partials %} {% partialdef my-partial %}
<!-- content -->
{% endpartialdef %}

<!-- After -->
{% partialdef my-partial %}
<!-- content -->
{% endpartialdef %}
```

### 4. 📦 Uninstall the Package

Remove the package from your environment:

```bash
pip uninstall django-template-partials
```

And remove it from your `requirements.txt`, `pyproject.toml`, or other dependency files.

## 📝 Notes

- ⚠️ Test your templates thoroughly after migration
- 📖 Check Django 6.0 release notes for any syntax changes or new features
- ✅ All existing functionality should work: partials, inline partials, and context handling
