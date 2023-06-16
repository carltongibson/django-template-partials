import django
from django.template import base, engines
import django.template.backends.django
from django.test import TestCase

from template_partials.templatetags.partials import TemplateProxy

class PartialTagsTestCase(TestCase):
    def test_partial_tags(self):
        template = """
        {% load partials %}
        {% startpartial "testing-partial" %}HERE IS THE TEST CONTENT{% endpartial %}
        {% partial "testing-partial" %}
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

    def test_just_partial_from_loader(self):
        engine = engines["django"]
        template = engine.get_template("example.html#test-partial")
        rendered = template.render()

        self.assertEqual("TEST-PARTIAL-CONTENT", rendered.strip())

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
        engine = engines["django"]
        template = engine.get_template("example.html#test-partial")
        self.assertIsInstance(template, django.template.backends.django.Template)
        self.assertIsInstance(template.template, TemplateProxy)
        self.assertTrue(hasattr(template.template, "source"))

        # Regular template
        template = engine.get_template("example.html")
        self.assertIsInstance(template, django.template.backends.django.Template)
        self.assertIsInstance(template.template, base.Template)
        self.assertTrue(hasattr(template.template,"source"))
