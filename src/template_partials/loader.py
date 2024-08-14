from django.template import TemplateDoesNotExist
from django.template.loaders import cached
from django.template.loaders.base import Loader as BaseLoader


class Loader(BaseLoader):
    """
    Wrapper class that takes a list of template loaders as an argument and attempts
    to load templates from them in order, before checking for a name `partial` on
    the template.

    By using the Loader, partials are transparent to the view and response layers.
    """

    def __init__(self, engine, loaders):
        self.loaders = engine.get_template_loaders(loaders)
        super().__init__(engine)

    def get_dirs(self):
        for loader in self.loaders:
            if hasattr(loader, "get_dirs"):
                yield from loader.get_dirs()

    def get_contents(self, origin):
        return origin.loader.get_contents(origin)

    def get_template(self, template_name, skip=None):
        """
        Steps:

        - Split the template_name into template_name, partial_name.
        - Use self.loaders to find the template. Raise if not found.
        - If partial_name is not None. Check for defined partial. Raise if not found.
        """
        template_name, _, partial_name = template_name.partition("#")

        # Find template from child loaders.
        # The cached loader requires special handling.
        # May raise TemplateDoesNotExist.
        if len(self.loaders) == 1 and isinstance(self.loaders[0], cached.Loader):
            template = self.loaders[0].get_template(template_name, skip)
        else:
            template = super().get_template(template_name, skip)

        if not partial_name:
            return template

        try:
            partial_contents = template.origin.partial_contents
        except AttributeError:
            # No partials defined on this template.
            raise TemplateDoesNotExist(partial_name, tried=[template_name])
        try:
            partial = partial_contents[partial_name]
        except KeyError:
            # Partial not found on this template.
            raise TemplateDoesNotExist(partial_name, tried=[template_name])
        partial.engine = self.engine

        return partial

    def get_template_sources(self, template_name):
        for loader in self.loaders:
            yield from loader.get_template_sources(template_name)

    def reset(self):
        for loader in self.loaders:
            try:
                loader.reset()
            except AttributeError:
                pass
