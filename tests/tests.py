from django.template import engines
from django.test import TestCase


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
