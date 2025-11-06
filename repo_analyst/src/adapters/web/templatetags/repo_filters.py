"""
Custom template filters for Repo-Analyst
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_attr(obj, attr_name):
    """
    Get an attribute from an object.
    Usage: {{ myobj|get_attr:"attribute_name" }}
    """
    try:
        return getattr(obj, attr_name)
    except (AttributeError, TypeError):
        return None
