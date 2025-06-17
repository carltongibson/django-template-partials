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

    def _render(self, context):
        return self.nodelist.render(context)

    def render(self, context):
        "Display stage -- can be called many times"
        with context.render_context.push_state(self):
            if context.template is None:
                with context.bind_template(self):
                    context.template_name = self.name
                    return self._render(context)
            else:
                return self._render(context)


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
    def __init__(self, partial_name, partial_mapping):
        # Defer lookup of nodelist to runtime.
        self.partial_name = partial_name
        self.partial_mapping = partial_mapping

    def render(self, context):
        return self.partial_mapping[self.partial_name].render(context)


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

    # Store the partial nodelist in the parser.extra_data attribute, if available. (Django 5.1+)
    # Otherwise, store it on the origin.
    if hasattr(parser, "extra_data"):
        parser.extra_data.setdefault("template-partials", {})
        parser.extra_data["template-partials"][partial_name] = TemplateProxy(
            nodelist, parser.origin, partial_name
        )
    else:
        if not hasattr(parser.origin, "partial_contents"):
            parser.origin.partial_contents = {}
        parser.origin.partial_contents[partial_name] = TemplateProxy(
            nodelist, parser.origin, partial_name
        )

    return DefinePartialNode(partial_name, inline, nodelist)


class SubDictionaryWrapper:
    """
    Wrap a parent dictionary, allowing deferred access to a sub-dictionary by key.

    The parser.extra_data storage may not yet be populated when a partial node
    is defined, so we defer access until rendering.
    """

    def __init__(self, parent_dict, lookup_key):
        self.parent_dict = parent_dict
        self.lookup_key = lookup_key

    def __getitem__(self, key):
        try:
            # Try Django 5.1+ dict-based storage first
            partials_content = self.parent_dict[self.lookup_key]
        except KeyError:
            raise template.TemplateSyntaxError(
                f"No partials are defined. You are trying to access '{key}' partial"
            )
        except TypeError:
            # Fall back to pre-Django 5.1 object-based storage
            try:
                partials_content = getattr(self.parent_dict, self.lookup_key)
            except AttributeError:
                raise template.TemplateSyntaxError(
                    f"No partials are defined. You are trying to access '{key}' partial"
                )

        try:
            return partials_content[key]
        except KeyError:
            raise template.TemplateSyntaxError(
                f"You are trying to access an undefined partial '{key}'"
            )


# Define the partial tag to render the partial content.
@register.tag(name="partial")
def partial_func(parser, token):
    """
    Render a partial that was previously declared using the {% partialdef %} or {% startpartial %} tag.

    Usage:

        {% partial partial_name %}
    """
    # Parse the tag
    try:
        tag_name, partial_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % tag_name
        )

    try:
        extra_data = getattr(parser, "extra_data")
        partial_mapping = SubDictionaryWrapper(extra_data, "template-partials")
    except AttributeError:
        partial_mapping = SubDictionaryWrapper(parser.origin, "partial_contents")

    return RenderPartialNode(partial_name, partial_mapping=partial_mapping)
