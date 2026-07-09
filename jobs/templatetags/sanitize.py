import bleach
from django import template

register = template.Library()

@register.filter(name='safe_html')
def safe_html(value):
    if not value:
        return ''
    allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'li', 'ol', 'a', 'b', 'i', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']
    allowed_attrs = {
        'a': ['href', 'target', 'rel'],
        'span': ['style'],
        'div': ['style'],
    }
    cleaned = bleach.clean(
        value, 
        tags=allowed_tags, 
        attributes=allowed_attrs, 
        strip=True
    )
    return cleaned
