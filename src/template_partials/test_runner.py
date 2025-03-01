from django.test.runner import DiscoverRunner
from django.test.signals import template_rendered


class TemplatePartialsTestRunner(DiscoverRunner):
    """
    Custom test runner that ensures template partials trigger Django's template_rendered signal,
    allowing test client to capture template context.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)

        try:
            # Get the Django template engine and access required classes and methods
            from template_partials.templatetags.partials import TemplateProxy

            # Store original methods
            self._original_template_proxy_render = TemplateProxy.render

            # Create a wrapper for TemplateProxy.render to handle partials
            def patched_template_proxy_render(proxy_self, context):
                # Get result from original render method first
                result = self._original_template_proxy_render(proxy_self, context)

                # Always send the template_rendered signal for the partial
                # This is the key part to make Django's test client work with partials
                template_rendered.send(
                    sender=proxy_self.__class__, template=proxy_self, context=context
                )

                return result

            # Apply the patches
            TemplateProxy.render = patched_template_proxy_render

        except Exception as e:
            print(f"Error setting up template test runner: {e}")

    def teardown_test_environment(self, **kwargs):
        # Restore the original methods if we patched them

        if self._original_template_proxy_render is not None:
            from template_partials.templatetags.partials import TemplateProxy

            TemplateProxy.render = self._original_template_proxy_render

        super().teardown_test_environment(**kwargs)
