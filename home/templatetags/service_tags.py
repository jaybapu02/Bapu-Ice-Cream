from django import template
from django.templatetags.static import static
import re

register = template.Library()

SERVICE_IMAGES = {
    'home-delivery': 'product2.png',
    'ice-cream-catering': '4.avif',
    'birthday-party-catering': '2.jpg',
    'wedding-event-catering': '12.avif',
    'corporate-event-catering': 'product1.png',
    'bulk-ice-cream-orders': 'product12.png',
    'custom-ice-cream-orders': 'Chocolate Delight.png',
    'party-packages': '1.avif',
}

@register.simple_tag
def service_static_image(service):
    slug = getattr(service, 'slug', '')
    filename = SERVICE_IMAGES.get(slug, 'hero-icecream.jpg')
    return static(filename)
