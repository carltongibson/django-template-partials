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
        """
        Display stage -- can be called many times
        """
        with context.render_context.push_state(self):
            if context.template is None:
                with context.bind_template(self):
                    context.template_name = self.name
                    return self.nodelist.render(context)
            else:
                return self.nodelist.render(context)


class DefinePartialNode(template.Node):
    def __init__(self, partial_name, inline, nodelist):
        self.partial_name = partial_name
        self.inline = inline
        self.nodelist = nodelist

    def render(self, context):
        """Set content into context and return empty string"""
        if self.inline:
            return self.nodelist.render(context)
        else:
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

        {% partialdef partial_name %}

        Partial content goes here

        {% endpartialdef %}

    Stores the nodelist in the context under the key "partial_contents" and can
    be retrieved using the {% partial %} tag.

    The optional inline=True argument will render the contents of the partial
    where it is defined.
    """
    return _define_partial(parser, token, "endpartialdef")


@register.tag(name="startpartial")
def startpartial_func(parser, token):
    warnings.warn(
        "The 'startpartial' tag is deprecated; use 'partialdef' instead.",
        DeprecationWarning,
    )
    return _define_partial(parser, token, "endpartial")


def _define_partial(parser, token, end_tag):
    # Parse the tag
    tokens = token.split_contents()

    # check we have the expected number of tokens before trying to assign them
    # via indexes
    if len(tokens) not in (2, 3):
        raise template.TemplateSyntaxError(
            "%r tag requires 2-3 arguments" % token.contents.split()[0]
        )

    partial_name = tokens[1]

    try:
        inline = tokens[2]
    except IndexError:
        # the inline argument is optional, so fallback to not using it
        inline = False

    # Parse the content until the end tag (`endpartialdef` or deprecated `endpartial`)
    acceptable_endpartials = (end_tag, f"{end_tag} {partial_name}")
    nodelist = parser.parse(acceptable_endpartials)
    endpartial = parser.next_token()
    if endpartial.contents not in acceptable_endpartials:
        parser.invalid_block_tag(endpartial, "endpartial", acceptable_endpartials)

    if not hasattr(parser.origin, "partial_contents"):
        parser.origin.partial_contents = {}
    parser.origin.partial_contents[partial_name] = TemplateProxy(
        nodelist, parser.origin, partial_name
    )

    return DefinePartialNode(partial_name, inline, nodelist)


# Define the partial tag to render the partial content.
@register.tag(name="partial")
def partial_func(parser, token):
    """
    Render a partial that was previously declared using the {% partialdef %} or {% startpartial %} tag.

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
