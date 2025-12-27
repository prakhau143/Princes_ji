from django import template
from store.models import Cart

register = template.Library()

@register.simple_tag(takes_context=True)
def cart_item_count(context):
    user = context['user']
    if user.is_authenticated:
        try:
            cart = Cart.objects.get(user=user)
            return cart.items.count()
        except Cart.DoesNotExist:
            return 0
    return 0
