"""
django-template-partials

Reusable named inline partials for the Django Template Language.
"""
from django.apps import AppConfig
from django.conf import settings


class LoaderAppConfig(AppConfig):
    name = "template_partials"
    default = True

    def ready(self):
        for template_config in settings.TEMPLATES:
            if template_config["BACKEND"] == "django.template.backends.django.DjangoTemplates":
                loaders = template_config.setdefault("OPTIONS", {}).get("loaders", [])
                already_configured = (loaders and isinstance(loaders, (list, tuple)) and
                                      isinstance(loaders[0], tuple) and
                                      loaders[0][0] == "template_partials.loader.Loader")
                if not already_configured:
                    template_config.pop("APP_DIRS", None)
                    default_loaders = [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ]
                    cached_loaders = [("django.template.loaders.cached.Loader", default_loaders)]
                    partial_loaders = [("template_partials.loader.Loader", cached_loaders)]
                    template_config['OPTIONS']['loaders'] = partial_loaders
                break


class BaseAppConfig(AppConfig):
    name = "template_partials"
