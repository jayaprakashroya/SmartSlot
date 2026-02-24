"""
Currency formatting utilities for Indian Rupees (INR)
Handles formatting with proper decimal precision and Lakhs/Crores display
"""

from decimal import Decimal
from django.conf import settings


def format_inr(amount, use_lakhs_crores=True):
    """
    Format amount as Indian Rupees with proper decimal handling
    
    Args:
        amount: Decimal or float value
        use_lakhs_crores: If True, use Indian numbering system (Lakhs/Crores)
    
    Returns:
        Formatted string with ₹ symbol
    
    Examples:
        format_inr(Decimal('50.50')) -> '₹50.50'
        format_inr(Decimal('100000')) -> '₹1.00L'
        format_inr(Decimal('10000000')) -> '₹1.00Cr'
    """
    if amount is None:
        return '₹0.00'
    
    try:
        # Ensure we're working with Decimal for precision
        if isinstance(amount, float):
            amount = Decimal(str(amount))
        elif not isinstance(amount, Decimal):
            amount = Decimal(amount)
        
        # Get absolute value for calculation
        abs_amount = abs(amount)
        is_negative = amount < 0
        
        if not use_lakhs_crores:
            # Simple formatting with 2 decimal places
            formatted = f"₹{amount:,.2f}"
            return formatted
        
        # Indian numbering system
        if abs_amount >= Decimal('10000000'):  # 1 Crore
            crores = amount / Decimal('10000000')
            formatted = f"₹{crores:.2f}Cr"
        elif abs_amount >= Decimal('100000'):  # 1 Lakh
            lakhs = amount / Decimal('100000')
            formatted = f"₹{lakhs:.2f}L"
        elif abs_amount >= Decimal('1000'):  # 1 Thousand
            thousands = amount / Decimal('1000')
            formatted = f"₹{thousands:,.2f}K"
        else:
            formatted = f"₹{amount:,.2f}"
        
        return formatted
    
    except Exception as e:
        return f'₹{amount}'


def format_inr_simple(amount):
    """Simple INR formatting without Lakhs/Crores"""
    return format_inr(amount, use_lakhs_crores=False)


def format_inr_indian_system(amount):
    """Format with full Indian numbering system (Lakhs/Crores)"""
    return format_inr(amount, use_lakhs_crores=True)


def format_decimal_field(amount, decimal_places=2):
    """
    Ensure amount is Decimal with specified decimal places
    Used for database operations to prevent float rounding errors
    """
    if amount is None:
        return Decimal('0.00')
    
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    elif not isinstance(amount, Decimal):
        amount = Decimal(amount)
    
    # Round to specified decimal places
    quantize_str = '0.' + '0' * decimal_places
    return amount.quantize(Decimal(quantize_str))


def indian_number_format(number):
    """
    Convert a number to Indian numbering system
    E.g., 1000 -> 1,000; 100000 -> 1,00,000
    """
    if number is None:
        return '0'
    
    try:
        # Convert to string and handle negative
        is_negative = number < 0
        number = abs(number)
        number_str = str(int(number))
        
        if len(number_str) <= 3:
            result = number_str
        else:
            # Apply Indian numbering system
            # Split into groups: last 3 digits, then groups of 2
            last_three = number_str[-3:]
            remaining = number_str[:-3]
            
            groups = []
            if remaining:
                # Process remaining digits in groups of 2 from right
                remaining_len = len(remaining)
                if remaining_len % 2 == 1:
                    groups.append(remaining[0])
                    remaining = remaining[1:]
                
                # Add groups of 2
                for i in range(0, len(remaining), 2):
                    groups.append(remaining[i:i+2])
            
            result = ','.join(groups) + (',' if groups else '') + last_three
        
        return ('-' + result) if is_negative else result
    
    except Exception:
        return str(number)


def calculate_fee(duration_minutes, hourly_rate=50):
    """
    Calculate parking fee with proper decimal precision
    
    Args:
        duration_minutes: Duration in minutes
        hourly_rate: Hourly rate in INR (default: ₹50/hr)
    
    Returns:
        Decimal with fee amount
    """
    try:
        duration_minutes = Decimal(str(duration_minutes))
        hourly_rate = Decimal(str(hourly_rate))
        
        # Calculate: (minutes / 60) * hourly_rate
        fee = (duration_minutes / Decimal('60')) * hourly_rate
        
        # Round to 2 decimal places
        return fee.quantize(Decimal('0.01'))
    
    except Exception as e:
        return Decimal('0.00')
