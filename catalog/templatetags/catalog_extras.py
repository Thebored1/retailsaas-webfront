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
