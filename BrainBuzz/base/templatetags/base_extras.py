from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if not hasattr(dictionary, 'get'):
        return None
    
    # Try the key as is, then try it as a string
    return dictionary.get(key) or dictionary.get(str(key))
