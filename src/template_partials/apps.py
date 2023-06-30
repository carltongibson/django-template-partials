"""
django-template-partials

App configuration to set up a partials loader automatically.
"""
from django.apps import AppConfig
from django.conf import settings


class LoaderAppConfig(AppConfig):
    """
    This, the default configuration, does the automatic setup of a partials loader.
    """
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
    """
    This, the non-default configuration, allows the user to opt-out of the automatic configuration. They just need to
    add "template_partials.apps.BaseAppConfig" to INSTALLED_APPS instead of "template_partials".
    """
    name = "template_partials"
