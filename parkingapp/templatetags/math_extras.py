from django import template

register = template.Library()


@register.filter(name='mul')
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except Exception:
        return 0


@register.filter(name='div')
def div(value, arg):
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except Exception:
        return 0


@register.filter(name='sub')
def sub(value, arg):
    try:
        return float(value) - float(arg)
    except Exception:
        return 0
