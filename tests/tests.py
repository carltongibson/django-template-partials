import warnings

from django.template import engines
from django.test import TestCase


class PartialTagsTestCase(TestCase):
    def test_partial_tags(self):
        template = """
        {% load partials %}
        {% partialdef "testing-partial" %}HERE IS THE TEST CONTENT{% endpartialdef %}
        {% partial "testing-partial" %}
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
        {% startpartial "deprecated-testing-partial" %}DEPRECATED TEST CONTENT{% endpartial %}
        {% partial "deprecated-testing-partial" %}
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
            self.assertTrue(any(issubclass(warn.category, DeprecationWarning) for warn in w))

        # Check the rendered content
        self.assertEqual("DEPRECATED TEST CONTENT", rendered.strip())

    def test_partialdef_tag_with_inline(self):
        template = """
        {% load partials %}
        {% partialdef "testing-partial" inline=True %}
        HERE IS THE TEST CONTENT
        {% endpartialdef %}
        """

        # Compile and render the template
        engine = engines["django"]
        t = engine.from_string(template)
        rendered = t.render()

        # Check the rendered content
        self.assertEqual("HERE IS THE TEST CONTENT", rendered.strip())

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
            template.render({'exception': LazyExceptionObject()})
        except Exception as e:
            self.assertEqual(e.template_debug['message'], "Test exception")
            self.assertEqual(e.template_debug['line'], 4)

    def test_template_source(self):
        """Partials defer to their source template for source code."""
        engine = engines["django"]
        partial = engine.get_template("example.html#test-partial")
        source_template = engine.get_template("example.html")
        self.assertEqual(
            partial.template.source,
            source_template.template.source,
        )
