from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def sub(value, arg):
    try:
        return value - arg
    except (ValueError, TypeError):
        return value


@register.filter
def b64_data_uri(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.startswith("data:"):
        return raw

    mime = "image/jpeg"
    if raw.startswith("iVBOR"):
        mime = "image/png"
    elif raw.startswith("R0lGOD"):
        mime = "image/gif"
    elif raw.startswith("UklGR"):
        mime = "image/webp"

    return f"data:{mime};base64,{raw}"
