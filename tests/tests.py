import sys
import warnings
from pathlib import Path
from textwrap import dedent
from unittest import mock

import django.template
from django.http import HttpResponse
from django.template import EngineHandler, TemplateSyntaxError, engines
from django.template.loader import render_to_string
from django.test import TestCase, override_settings

from template_partials.apps import wrap_loaders


@override_settings(
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
        },
    ]
)
class SimpleAppConfigTestCase(TestCase):
    def test_wrap_loaders(self):
        django.template.engines = EngineHandler()

        outermost_loader = django.template.engines["django"].engine.loaders[0][0]
        assert outermost_loader != "template_partials.loader.Loader"

        wrap_loaders("django")

        outermost_loader = django.template.engines["django"].engine.loaders[0][0]
        assert outermost_loader == "template_partials.loader.Loader"


class PartialTagsTestCase(TestCase):
    def test_partial_tags(self):
        template = """
        {% load partials %}
        {% partialdef testing-partial %}HERE IS THE TEST CONTENT{% endpartialdef %}
        {% partial testing-partial %}
        """

        # Compile and render the template
        engine = engines["django"]
        t = engine.from_string(template)
        rendered = t.render()

        # Check the rendered content
        self.assertEqual("HERE IS THE TEST CONTENT", rendered.strip())

    def test_deprecated_startpartial_tag(self):
        template = """
        {% load partials %}
        {% startpartial deprecated-testing-partial %}DEPRECATED TEST CONTENT{% endpartial %}
        {% partial deprecated-testing-partial %}
        """

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            # Compile and render the template
            engine = engines["django"]
            t = engine.from_string(template)
            rendered = t.render()

            # Check for deprecation warning
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn(
                "The 'startpartial' tag is deprecated; use 'partialdef' instead.",
                str(w[-1]),
            )

        # Check the rendered content
        self.assertEqual("DEPRECATED TEST CONTENT", rendered.strip())

    def test_partialdef_tag_with_inline(self):
        template = """
        {% load partials %}
        {% partialdef testing-partial inline %}
        HERE IS THE TEST CONTENT
        {% endpartialdef %}
        """

        # Compile and render the template
        engine = engines["django"]
        t = engine.from_string(template)
        rendered = t.render()

        # Check the rendered content
        self.assertEqual("HERE IS THE TEST CONTENT", rendered.strip())

    def test_inline_partial_with_wrapping_content(self):
        template = """
        {% load partials %}
        BEFORE
        {% partialdef testing-partial inline %}
        HERE IS THE TEST CONTENT
        {% endpartialdef %}
        AFTER
        """

        # Compile and render the template
        engine = engines["django"]
        t = engine.from_string(dedent(template))
        rendered = t.render()

        # Check the rendered content
        self.assertEqual(
            "BEFORE\n\nHERE IS THE TEST CONTENT\n\nAFTER", rendered.strip()
        )

    def test_deprecated_inline_argument(self):
        template = """
        {% load partials %}
        {% partialdef testing-partial inline=True %}TEST CONTENT{% endpartialdef %}
        """

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            # Compile and render the template
            engine = engines["django"]
            t = engine.from_string(template)
            rendered = t.render()

            # Check for deprecation warning
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn(
                "The 'inline' argument does not have any parameters", str(w[-1])
            )

        # Check the rendered content
        self.assertEqual("TEST CONTENT", rendered.strip())

    def test_endpartialdef_with_partial_name(self):
        template = """
        {% load partials %}
        {% partialdef testing-partial %}
        HERE IS THE TEST CONTENT
        {% endpartialdef testing-partial %}
        {% partial testing-partial %}
        """

        # Compile and render the template
        engine = engines["django"]
        t = engine.from_string(template)
        rendered = t.render()

        # Check the rendered content
        self.assertEqual("HERE IS THE TEST CONTENT", rendered.strip())

    def test_endpartialdef_with_invalid_partial_name(self):
        template = """
        {% load partials %}
        {% partialdef testing-partial %}
        HERE IS THE TEST CONTENT
        {% endpartialdef invalid %}
        {% partial testing-partial %}
        """

        with self.assertRaises(TemplateSyntaxError):
            # Compile and render the template
            engine = engines["django"]
            engine.from_string(template)

    def test_full_template_from_loader(self):
        engine = engines["django"]
        template = engine.get_template("example.html")
        rendered = template.render()

        # Check the partial was rendered twice
        self.assertEqual(2, rendered.count("TEST-PARTIAL-CONTENT"))
        self.assertEqual(1, rendered.count("INLINE-CONTENT"))

    def test_just_partial_from_loader(self):
        engine = engines["django"]

        template = engine.get_template("example.html#test-partial")
        rendered = template.render()
        self.assertEqual("TEST-PARTIAL-CONTENT", rendered.strip())

        template = engine.get_template("example.html#inline-partial")
        rendered = template.render()
        self.assertEqual("INLINE-CONTENT", rendered.strip())

    def test_debug_template(self):
        class LazyExceptionObject:
            def __str__(self):
                raise Exception("Test exception")

        engine = engines["django"]
        template = engine.get_template("debug.html")
        try:
            template.render({"exception": LazyExceptionObject()})
        except Exception as e:
            self.assertEqual(e.template_debug["message"], "Test exception")
            self.assertEqual(e.template_debug["line"], 4)

    def test_template_source(self):
        """Partials defer to their source template for source code."""
        engine = engines["django"]
        partial = engine.get_template("example.html#test-partial")
        self.assertEqual(partial.template.source, "\nTEST-PARTIAL-CONTENT\n")
        partial = engine.get_template("example.html#inline-partial")
        self.assertEqual(partial.template.source, "\nINLINE-CONTENT\n")

    def test_chained_exception_forwarded(self):
        """TemplateDoesNotExist exceptions are chained with the tried attribute."""
        engine = engines["django"]
        with self.assertRaises(django.template.TemplateDoesNotExist) as ex:
            engine.get_template("not_there.html#not-a-partial")

        self.assertTrue(len(ex.exception.tried) > 0)
        origin, _ = ex.exception.tried[0]
        self.assertEqual(origin.template_name, "not_there.html")

    def test_extends_with_partialdef(self):
        """
        Regression test for issue #26: When TemplateProxy lacks get_nodes_by_type,
        using extends and partialdef together should work now
        """

        # Template with both extends and partialdef
        template_string = """
        {% extends 'base.html' %}
        {% load partials %}
        {% partialdef test-partial %}
        Content inside partial
        {% endpartialdef %}
        {% block main %}
        Main content with {% partial test-partial %}
        {% endblock %}
        """

        engine = engines["django"]
        template = engine.from_string(template_string)
        rendered = template.render()

        # Verify the template rendered correctly
        self.assertIn("Main content with", rendered)
        self.assertIn("Content inside partial", rendered)

    def test_template_inclusion_with_partial(self):
        """
        Test that a template can include another template that defines and uses a partial.
        """
        engine = engines["django"]
        parent_template = engine.get_template("parent.html")
        rendered = parent_template.render()
        self.assertIn("MAIN TEMPLATE START", rendered)
        self.assertIn("INCLUDED TEMPLATE START", rendered)
        self.assertIn("THIS IS CONTENT FROM THE INCLUDED PARTIAL", rendered)
        self.assertIn("INCLUDED TEMPLATE END", rendered)
        self.assertIn("MAIN TEMPLATE END", rendered)

    def test_using_partial_before_definition(self):
        """
        Test using a partial before it's defined in the template.
        """
        template_content = """
        {% load partials %}
        TEMPLATE START
        {% partial skeleton-partial %}
        MIDDLE CONTENT
        {% partialdef skeleton-partial %}
        THIS IS THE SKELETON PARTIAL CONTENT
        {% endpartialdef %}
        TEMPLATE END
        """
        engine = engines["django"]
        template = engine.from_string(template_content)
        rendered = template.render()
        self.assertIn("TEMPLATE START", rendered)
        self.assertIn("THIS IS THE SKELETON PARTIAL CONTENT", rendered)
        self.assertIn("MIDDLE CONTENT", rendered)
        self.assertIn("TEMPLATE END", rendered)

    def test_undefined_partial_error_message(self):
        """
        Test that an undefined partial raises a TemplateSyntaxError.
        """
        template = """
        {% load partials %}
        {% partialdef different-partial %}
        THIS IS THE NOT DEFINED PARTIAL CONTENT
        {% endpartialdef %}
        {% partial not-defined-partial %}
        """

        # Compile and render the template
        engine = engines["django"]
        t = engine.from_string(template)
        with self.assertRaisesMessage(
            TemplateSyntaxError,
            "You are trying to access an undefined partial 'not-defined-partial'",
        ):
            t.render()

    def test_undefined_partial_error_message_when_no_partialdef(self):
        """
        Test that an undefined partial raises a TemplateSyntaxError.
        """
        template = """
        {% load partials %}
        {% partial not-defined-partial %}
        """
        engine = engines["django"]
        t = engine.from_string(template)
        with self.assertRaisesMessage(
            TemplateSyntaxError,
            "No partials are defined. You are trying to access 'not-defined-partial' partial",
        ):
            t.render()

    def test_partial_with_no_partial_name(self):
        """
        Test that a partial with no partial name raises a TemplateSyntaxError.
        """
        template = """
        {% load partials %}
        {% partial %}
        """
        engine = engines["django"]
        with self.assertRaisesMessage(
            TemplateSyntaxError,
            "'partial' tag requires a single argument 'partial_name'",
        ):
            engine.from_string(template)


class ChildCachedLoaderTest(TestCase):
    def test_child_cached_loader(self):
        wrap_loaders("django")
        engine = engines["django"].engine
        partial_loader = engine.template_loaders[0]
        self.assertEqual(type(partial_loader).__module__, "template_partials.loader")
        cached_loader = partial_loader.loaders[0]
        self.assertEqual(
            type(cached_loader).__module__, "django.template.loaders.cached"
        )
        self.assertEqual(len(cached_loader.get_template_cache), 0)
        template = engine.get_template("example.html")
        self.assertEqual(len(cached_loader.get_template_cache), 1)

        # Simulate a template change and check the cache is reset.
        django.template.autoreload.template_changed(None, Path(template.origin.name))
        self.assertEqual(len(cached_loader.get_template_cache), 0)


class ResponseWithMultiplePartsTests(TestCase):
    def test_resonse_with_multiple_parts(self):
        context = {}  # Your context here.
        template_partials = ["child.html", "child.html#extra-content"]

        # Stragegy 1: Combine in view.
        response_content = ""
        for template_name in template_partials:
            response_content += render_to_string(template_name, context)

        response1 = HttpResponse(response_content)

        # Stragegy 2: Use as a file-like object.
        response2 = HttpResponse()
        for template_name in template_partials:
            response2.write(render_to_string(template_name, context))

        # Stragegy 3: Use with a generator expression.
        response3 = HttpResponse(
            render_to_string(template_name, context)
            for template_name in template_partials
        )

        for response in [response1, response2, response3]:
            self.assertIn(b"Main Content", response.content)
            self.assertIn(b"Extra Content", response.content)

    @mock.patch("django.VERSION", (6, 0))
    def test_load_partial_deprecation_warning(self):
        if "template_partials.templatetags.partials" in sys.modules:
            del sys.modules["template_partials.templatetags.partials"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import template_partials.templatetags.partials  # noqa: F401

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            self.assertEqual(len(deprecation_warnings), 1)
            self.assertIn(
                "The 'partial'and 'partialdef' template tags are now part of Django core",
                str(deprecation_warnings[0].message),
            )
            self.assertIn(
                "You no longer need to use {% load partials %}",
                str(deprecation_warnings[0].message),
            )
