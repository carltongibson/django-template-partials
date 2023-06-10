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
    "tests",
]

# Additional settings.
DEBUG = True
SECRET_KEY = "a-not-very-secret-test-secret-key"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}
