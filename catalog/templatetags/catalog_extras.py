from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)
