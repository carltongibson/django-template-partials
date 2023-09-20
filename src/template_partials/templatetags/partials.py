import warnings

from django import template

register = template.Library()


class TemplateProxy:
    """
    Wraps nodelist as partial, in order to bind context.
    """

    def __init__(self, nodelist, origin, name):
        self.nodelist = nodelist
        self.origin = origin
        self.name = name

    def get_exception_info(self, exception, token):
        template = self.origin.loader.get_template(self.origin.template_name)
        return template.get_exception_info(exception, token)

    @property
    def source(self):
        template = self.origin.loader.get_template(self.origin.template_name)
        return template.source

    def render(self, context):
        "Display stage -- can be called many times"
        with context.render_context.push_state(self):
            if context.template is None:
                with context.bind_template(self):
                    context.template_name = self.name
                    return self.nodelist.render(context)
            else:
                return self.nodelist.render(context)


class DefinePartialNode(template.Node):
    def __init__(self, partial_name, nodelist):
        self.partial_name = partial_name
        self.nodelist = nodelist

    def render(self, context):
        """Set content into context and return empty string"""
        return ""


class RenderPartialNode(template.Node):
    def __init__(self, partial_name, origin):
        self.partial_name = partial_name
        self.origin = origin

    def render(self, context):
        """Render the partial content from the context"""
        # Use the origin to get the partial content, because it's per Template,
        # and available to the Parser.
        # TODO: raise a better error here.
        nodelist = self.origin.partial_contents[self.partial_name]
        return nodelist.render(context)

@register.tag(name="partialdef")
def partialdef_func(parser, token):
    """
    Declare a partial that can be used later in the template.

    Usage:

        {% partialdef "partial_name" %}

        Partial content goes here

        {% endpartialdef %}

    Stores the nodelist in the context under the key "partial_contents" and can
    be retrieved using the {% partial %} tag.
    """
    return _define_partial(parser, token, "endpartialdef")

@register.tag(name="startpartial")
def startpartial_func(parser, token):
    warnings.warn(
        "The 'startpartial' tag is deprecated; use 'partialdef' instead.",
        DeprecationWarning
    )
    return _define_partial(parser, token, "endpartial")

def _define_partial(parser, token, end_tag):
    try:
        tag_name, partial_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )

    nodelist = parser.parse((end_tag,))
    parser.delete_first_token()

    if not hasattr(parser.origin, "partial_contents"):
        parser.origin.partial_contents = {}
    parser.origin.partial_contents[partial_name] = TemplateProxy(
        nodelist, parser.origin, partial_name
    )

    return DefinePartialNode(partial_name, nodelist)

# Define the partial tag to render the partial content.
@register.tag(name="partial")
def partial_func(parser, token):
    """
    Render a partial that was previously declared using the {% startpartial %} tag.

    Usage:

        {% partial "partial_name" %}
    """
    # Parse the tag
    try:
        tag_name, partial_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )

    return RenderPartialNode(partial_name, origin=parser.origin)

    pass
