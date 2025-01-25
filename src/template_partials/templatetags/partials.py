import re
import warnings

from django import template
from django.utils.autoreload import file_changed

register = template.Library()

#
# A mapping of template paths to a mapping of sources of partials in that template.
# This acts as a cache of the partial sources. The on_file_change function invalidates
# the cache when needed.
#
_PARTIALS_MAP = {
}

_START_TAG = re.compile(r'\{%\s*(startpartial|partialdef)\s+([\w-]+)(\s+inline)?\s*%}')
_END_TAG_OLD = re.compile(r'\{%\s*endpartial\s*%}')
_END_TAG = re.compile(r'\{%\s*endpartialdef\s*%}')


def on_file_change(sender, file_path, **kwargs):
    s = str(file_path)  # Convert from a Path object
    _PARTIALS_MAP.pop(s, None)  # Clear the cache for a changed template


file_changed.connect(on_file_change, dispatch_uid='on-file-change')


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

    def populate_partials_map(self, full_source):
        """
        Loop through the full source of the template, looking for partials.
        Return a dict mapping partial names to their sources.
        """
        result = {}
        pos = 0
        for m in _START_TAG.finditer(full_source, pos):
            sspos, sepos = m.span()
            starter, name, inline = m.groups()
            end_tag = _END_TAG_OLD if starter == 'startpartial' else _END_TAG
            endm = end_tag.search(full_source, sepos + 1)
            assert endm, 'End tag must be present'
            espos, eepos = endm.span()
            result[name] = full_source[sepos:espos]
            pos = eepos + 1
        return result

    @property
    def source(self):
        name = self.origin.name  # Should be the path to the containing template
        if name in _PARTIALS_MAP:
            partials_map = _PARTIALS_MAP[name]
        else:
            template = self.origin.loader.get_template(name)
            full_source = template.source
            partials_map = self.populate_partials_map(full_source)
            _PARTIALS_MAP[name] = partials_map
        return partials_map[self.name]

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

    The optional ``inline`` argument will render the contents of the partial
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

    if inline and inline != "inline":
        warnings.warn(
            "The 'inline' argument does not have any parameters; either use 'inline' or remove it completely.",
            DeprecationWarning,
        )

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
