"""
Payment Service for Smart Parking System
Handles payment processing, invoicing, and transaction management
"""
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import json
from datetime import datetime


class PaymentService:
    """Service for handling payment processing"""
    
    @staticmethod
    def calculate_parking_fee(vehicle, entry_time, exit_time=None):
        """Calculate parking fee based on duration"""
        if exit_time is None:
            exit_time = timezone.now()
        
        duration = (exit_time - entry_time).total_seconds() / 3600  # Hours
        
        # Pricing tiers
        if duration <= 1:
            fee = Decimal('5.00')  # First hour: $5
        elif duration <= 2:
            fee = Decimal('8.00')  # Second hour: $8
        elif duration <= 4:
            fee = Decimal('15.00')  # Up to 4 hours: $15
        else:
            # $15 base + $3 per additional hour, max $50/day
            additional_hours = duration - 4
            fee = Decimal('15.00') + (Decimal(additional_hours) * Decimal('3.00'))
            fee = min(fee, Decimal('50.00'))
        
        return round(fee, 2)
    
    @staticmethod
    def create_invoice(vehicle_id, parking_lot_id, entry_time, exit_time, amount):
        """Create payment invoice record"""
        invoice_id = str(uuid.uuid4())[:8].upper()
        
        invoice_data = {
            'invoice_id': f'INV-{invoice_id}',
            'vehicle_id': vehicle_id,
            'parking_lot_id': parking_lot_id,
            'entry_time': entry_time.isoformat() if hasattr(entry_time, 'isoformat') else str(entry_time),
            'exit_time': exit_time.isoformat() if hasattr(exit_time, 'isoformat') else str(exit_time),
            'amount': str(amount),
            'currency': 'USD',
            'status': 'paid',
            'payment_date': timezone.now().isoformat(),
            'payment_method': 'card',
            'transaction_id': str(uuid.uuid4())[:12].upper()
        }
        
        return invoice_data
    
    @staticmethod
    def process_payment(amount, vehicle_id, method='mock'):
        """Process payment through payment gateway"""
        if method == 'mock':
            # Mock payment for testing
            return {
                'success': True,
                'transaction_id': str(uuid.uuid4())[:12].upper(),
                'amount': amount,
                'status': 'completed',
                'timestamp': timezone.now().isoformat()
            }
        
        elif method == 'stripe':
            # Stripe integration would go here
            try:
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                
                intent = stripe.PaymentIntent.create(
                    amount=int(float(amount) * 100),  # Convert to cents
                    currency='usd',
                    metadata={'vehicle_id': vehicle_id}
                )
                
                return {
                    'success': True,
                    'transaction_id': intent.id,
                    'amount': amount,
                    'status': 'processing',
                    'client_secret': intent.client_secret
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'status': 'failed'
                }
        
        return {'success': False, 'error': 'Unknown payment method'}
    
    @staticmethod
    def generate_receipt(invoice_data, vehicle_info=None):
        """Generate receipt text for email"""
        receipt = f"""
╔══════════════════════════════════════════════════════════════╗
║              SMART PARKING SYSTEM RECEIPT                    ║
╚══════════════════════════════════════════════════════════════╝

INVOICE ID: {invoice_data['invoice_id']}
Transaction ID: {invoice_data['transaction_id']}
Status: {invoice_data['status'].upper()}

VEHICLE INFORMATION:
  License Plate: {vehicle_info.get('plate', 'N/A') if vehicle_info else 'N/A'}
  Vehicle Type: {vehicle_info.get('type', 'N/A') if vehicle_info else 'N/A'}

PARKING DETAILS:
  Entry Time: {invoice_data['entry_time']}
  Exit Time: {invoice_data['exit_time']}
  Parking Location: Lot {invoice_data['parking_lot_id']}

PAYMENT INFORMATION:
  Amount: {invoice_data['currency']} {invoice_data['amount']}
  Payment Method: {invoice_data['payment_method'].title()}
  Payment Date: {invoice_data['payment_date']}

═══════════════════════════════════════════════════════════════
Thank you for using Smart Parking System!
For support: support@smartparking.com
═══════════════════════════════════════════════════════════════
"""
        return receipt.strip()


class MockPaymentGateway:
    """Mock payment gateway for testing"""
    
    @staticmethod
    def validate_card(card_number):
        """Validate credit card format (mock)"""
        return len(card_number) == 16 and card_number.isdigit()
    
    @staticmethod
    def process_transaction(amount, card_info):
        """Process mock transaction"""
        if not MockPaymentGateway.validate_card(card_info.get('number', '')):
            return {'success': False, 'error': 'Invalid card'}
        
        return {
            'success': True,
            'transaction_id': f'TXN-{uuid.uuid4().hex[:10].upper()}',
            'amount': amount,
            'timestamp': timezone.now().isoformat()
        }
