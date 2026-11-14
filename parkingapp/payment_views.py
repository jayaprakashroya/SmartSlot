"""
Payment API Views for Smart Parking System
REST endpoints for payment processing and invoice management
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from parkingapp.models import ParkingLot, Vehicle
from parkingapp.payment_service import PaymentService
from parkingapp.email_service import EmailNotificationService
from parkingapp.rbac import permission_required, RoleManager
import json
from decimal import Decimal
from django.utils import timezone


@require_http_methods(["POST"])
def calculate_fee(request):
    """Calculate parking fee based on duration"""
    try:
        data = json.loads(request.body)
        vehicle_id = data.get('vehicle_id')
        entry_time_str = data.get('entry_time')
        exit_time_str = data.get('exit_time')
        
        if not all([vehicle_id, entry_time_str]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)
        
        # Parse times
        from datetime import datetime
        entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
        
        if exit_time_str:
            exit_time = datetime.fromisoformat(exit_time_str.replace('Z', '+00:00'))
        else:
            exit_time = timezone.now()
        
        # Get vehicle
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Calculate fee
        fee = PaymentService.calculate_parking_fee(vehicle, entry_time, exit_time)
        
        return JsonResponse({
            'success': True,
            'vehicle_id': vehicle_id,
            'vehicle_plate': vehicle.license_plate,
            'fee': float(fee),
            'currency': 'USD',
            'entry_time': entry_time_str,
            'exit_time': exit_time_str or timezone.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def create_invoice(request):
    """Create and process payment invoice"""
    try:
        data = json.loads(request.body)
        
        required_fields = ['vehicle_id', 'parking_lot_id', 'entry_time', 'exit_time', 'amount']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Parse times
        from datetime import datetime
        entry_time = datetime.fromisoformat(data['entry_time'].replace('Z', '+00:00'))
        exit_time = datetime.fromisoformat(data['exit_time'].replace('Z', '+00:00'))
        amount = Decimal(str(data['amount']))
        
        # Create invoice
        invoice = PaymentService.create_invoice(
            data['vehicle_id'],
            data['parking_lot_id'],
            entry_time,
            exit_time,
            amount
        )
        
        # Process payment
        payment_result = PaymentService.process_payment(amount, data['vehicle_id'])
        
        if payment_result['success']:
            invoice.update(payment_result)
            
            # Send receipt email if user provided
            user_email = data.get('user_email')
            if user_email:
                vehicle = Vehicle.objects.get(id=data['vehicle_id'])
                receipt_text = PaymentService.generate_receipt(
                    invoice,
                    {'plate': vehicle.license_plate, 'type': vehicle.vehicle_type}
                )
                EmailNotificationService.send_parking_receipt(user_email, receipt_text, invoice)
            
            return JsonResponse({
                'success': True,
                'invoice': invoice
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Payment processing failed',
                'details': payment_result
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def process_payment(request):
    """Process payment transaction"""
    try:
        data = json.loads(request.body)
        
        required_fields = ['amount', 'vehicle_id', 'method']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        amount = Decimal(str(data['amount']))
        vehicle_id = data['vehicle_id']
        method = data.get('method', 'mock')
        
        # Process payment
        result = PaymentService.process_payment(amount, vehicle_id, method)
        
        if result['success']:
            # Send confirmation email
            user_email = data.get('user_email')
            if user_email:
                EmailNotificationService.send_payment_confirmation(user_email, result)
            
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def payment_history(request):
    """Get user's payment history"""
    try:
        # This would typically query a Payment model
        # For now, returning sample data
        history = [
            {
                'invoice_id': 'INV-ABC12345',
                'amount': '25.50',
                'date': '2024-01-15T14:30:00Z',
                'status': 'paid',
                'vehicle': 'ABC-1234'
            },
            {
                'invoice_id': 'INV-XYZ98765',
                'amount': '15.00',
                'date': '2024-01-14T10:15:00Z',
                'status': 'paid',
                'vehicle': 'ABC-1234'
            }
        ]
        
        return JsonResponse({
            'success': True,
            'history': history,
            'total_paid': sum(Decimal(item['amount']) for item in history),
            'count': len(history)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def invoice_detail(request, invoice_id):
    """Get invoice details"""
    try:
        # This would query the Invoice model in production
        invoice = {
            'invoice_id': invoice_id,
            'vehicle_id': 'VEH-001',
            'vehicle_plate': 'ABC-1234',
            'parking_lot': 'Downtown A',
            'entry_time': '2024-01-15T10:30:00Z',
            'exit_time': '2024-01-15T14:45:00Z',
            'duration_hours': 4.25,
            'amount': '25.50',
            'currency': 'USD',
            'status': 'paid',
            'payment_date': '2024-01-15T14:45:00Z',
            'transaction_id': 'TXN-ABC123DEF456'
        }
        
        return JsonResponse({
            'success': True,
            'invoice': invoice
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def payment_status(request, transaction_id):
    """Check payment status"""
    try:
        status = {
            'transaction_id': transaction_id,
            'status': 'completed',
            'amount': '25.50',
            'currency': 'USD',
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'status': status
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
