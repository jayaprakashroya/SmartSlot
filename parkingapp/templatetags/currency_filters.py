"""
Django template tags and filters for currency formatting
Usage in templates:
    {{ amount|inr }}
    {{ amount|inr_simple }}
    {{ number|indian_format }}
"""

from django import template
from django.utils.safestring import mark_safe
from parkingapp.utils_currency import (
    format_inr,
    format_inr_simple,
    indian_number_format,
)

register = template.Library()


@register.filter(name='inr')
def inr_filter(value):
    """
    Format value as Indian Rupees with Lakhs/Crores support
    Usage: {{ amount|inr }}
    """
    try:
        return mark_safe(format_inr(value, use_lakhs_crores=True))
    except Exception:
        return f'₹{value}'


@register.filter(name='inr_simple')
def inr_simple_filter(value):
    """
    Format value as Indian Rupees without Lakhs/Crores
    Usage: {{ amount|inr_simple }}
    """
    try:
        return mark_safe(format_inr_simple(value))
    except Exception:
        return f'₹{value}'


@register.filter(name='indian_format')
def indian_format_filter(value):
    """
    Format number in Indian numbering system (1,00,000 instead of 100,000)
    Usage: {{ number|indian_format }}
    """
    try:
        return mark_safe(indian_number_format(value))
    except Exception:
        return str(value)


@register.filter(name='inr_amount')
def inr_amount_filter(value):
    """
    Alias for inr filter - format as INR with symbol
    Usage: {{ amount|inr_amount }}
    """
    try:
        return mark_safe(format_inr(value, use_lakhs_crores=False))
    except Exception:
        return f'₹{value}'
