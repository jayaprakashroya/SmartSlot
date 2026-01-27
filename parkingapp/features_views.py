"""
Advanced Features for Smart Parking System
- Parking Duration Tracking
- Payment Processing
- Reservations
- Notifications
- Analytics & Reports
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
import logging

from parkingapp.models import (
    User_details, ParkingSession, ParkingReservation, 
    Payment, UserNotification, ParkingAnalytics, 
    ParkingLot, PricingRule, ParkingLotSettings
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# FEATURE 1: PARKING HISTORY & DURATION TRACKING
# ═══════════════════════════════════════════════════════════════════

@login_required
def parking_history(request):
    """View user's parking history and sessions"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        sessions = ParkingSession.objects.filter(user=user).order_by('-entry_time')
        
        # Calculate statistics
        total_sessions = sessions.count()
        total_spent = sessions.aggregate(Sum('parking_fee'))['parking_fee__sum'] or 0
        avg_duration = sessions.aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
        
        # Active parking session
        active_session = sessions.filter(exit_time__isnull=True).first()
        
        context = {
            'sessions': sessions[:50],  # Last 50 sessions
            'total_sessions': total_sessions,
            'total_spent': total_spent,
            'avg_duration': round(avg_duration, 0),
            'active_session': active_session,
        }
        
        return render(request, 'parking_history.html', context)
    except Exception as e:
        logger.error(f"Parking history error: {str(e)}")
        messages.error(request, "Error loading parking history.")
        return redirect('dashboard')


@login_required
def end_parking_session(request, session_id):
    """End active parking session and calculate fees"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        session = ParkingSession.objects.get(session_id=session_id, user=user)
        
        if session.exit_time:
            messages.error(request, "This session has already ended.")
            return redirect('parking_history')
        
        # Calculate duration and fees
        session.exit_time = timezone.now()
        session.duration_minutes = session.calculate_duration()
        
        # Calculate parking fee based on duration
        pricing = PricingRule.objects.filter(
            parking_lot=session.parking_lot,
            vehicle_type=session.vehicle_type
        ).first()
        
        if pricing:
            hours = session.duration_minutes / 60
            if pricing.first_hour_free and hours <= 1:
                session.parking_fee = 0
            else:
                fee = (hours * pricing.base_rate)
                if pricing.max_daily_charge:
                    fee = min(fee, pricing.max_daily_charge)
                session.parking_fee = round(fee, 2)
        
        session.payment_status = 'pending'
        session.save()
        
        messages.success(request, f"Parking session ended. Total fee: ${session.parking_fee}")
        return redirect('parking_history')
    except Exception as e:
        logger.error(f"End session error: {str(e)}")
        messages.error(request, "Error ending parking session.")
        return redirect('parking_history')


# ═══════════════════════════════════════════════════════════════════
# FEATURE 2: PAYMENT PROCESSING
# ═══════════════════════════════════════════════════════════════════

@login_required
def payments(request):
    """View and manage payments"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        
        # Payment summary
        total_paid = payments.filter(payment_status='success').aggregate(Sum('amount'))['amount__sum'] or 0
        pending_payments = payments.filter(payment_status='pending')
        
        context = {
            'payments': payments[:20],
            'total_paid': total_paid,
            'pending_count': pending_payments.count(),
            'pending_amount': pending_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
        }
        
        return render(request, 'payments.html', context)
    except Exception as e:
        logger.error(f"Payments view error: {str(e)}")
        messages.error(request, "Error loading payments.")
        return redirect('dashboard')


@login_required
def process_payment(request, session_id):
    """Process payment for parking session"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        session = ParkingSession.objects.get(session_id=session_id, user=user)
        
        if session.payment_status == 'paid':
            messages.info(request, "This session is already paid.")
            return redirect('parking_history')
        
        if request.method == 'POST':
            payment_method = request.POST.get('payment_method', 'credit_card')
            
            # Create payment record
            payment = Payment.objects.create(
                parking_session=session,
                user=user,
                amount=session.parking_fee,
                payment_method=payment_method,
                payment_status='success',  # In real system: integrate payment gateway
                transaction_id=f"TXN-{timezone.now().timestamp()}"
            )
            
            # Update session
            session.payment_status = 'paid'
            session.save()
            
            # Create notification
            UserNotification.objects.create(
                user=user,
                notification_type='parking_complete',
                title='Payment Successful',
                message=f'Payment of ${session.parking_fee} confirmed for parking session'
            )
            
            messages.success(request, f"Payment of ${session.parking_fee} processed successfully!")
            return redirect('parking_history')
        
        context = {
            'session': session,
            'amount': session.parking_fee,
        }
        return render(request, 'process_payment.html', context)
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        messages.error(request, "Error processing payment.")
        return redirect('parking_history')


# ═══════════════════════════════════════════════════════════════════
# FEATURE 3: RESERVATIONS
# ═══════════════════════════════════════════════════════════════════

@login_required
def reserve_parking(request):
    """Make a parking reservation"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        lots = ParkingLot.objects.all()
        
        if request.method == 'POST':
            lot_id = request.POST.get('parking_lot')
            reserved_from = request.POST.get('reserved_from')
            reserved_until = request.POST.get('reserved_until')
            vehicle_type = request.POST.get('vehicle_type', 'car')
            license_plate = request.POST.get('license_plate', '')
            
            # Validate
            if not all([lot_id, reserved_from, reserved_until]):
                messages.error(request, "Please fill in all fields.")
                return render(request, 'reserve_parking.html', {'lots': lots})
            
            try:
                lot = ParkingLot.objects.get(lot_id=lot_id)
                from_dt = datetime.fromisoformat(reserved_from)
                to_dt = datetime.fromisoformat(reserved_until)
                
                if from_dt >= to_dt:
                    messages.error(request, "End time must be after start time.")
                    return render(request, 'reserve_parking.html', {'lots': lots})
                
                if from_dt < timezone.now():
                    messages.error(request, "Cannot reserve for past dates.")
                    return render(request, 'reserve_parking.html', {'lots': lots})
                
                # Calculate reservation fee (15% of estimated parking fee)
                duration_hours = (to_dt - from_dt).total_seconds() / 3600
                pricing = PricingRule.objects.filter(parking_lot=lot, vehicle_type=vehicle_type).first()
                
                reservation_fee = 0
                if pricing:
                    estimated_fee = duration_hours * pricing.base_rate
                    reservation_fee = round(estimated_fee * 0.15, 2)  # 15% reservation fee
                
                # Create reservation
                reservation = ParkingReservation.objects.create(
                    user=user,
                    parking_lot=lot,
                    reserved_from=from_dt,
                    reserved_until=to_dt,
                    vehicle_type=vehicle_type,
                    license_plate=license_plate,
                    reservation_fee=reservation_fee,
                    status='active'
                )
                
                messages.success(request, f"Reservation successful! Reservation fee: ${reservation_fee}")
                return redirect('my_reservations')
            except Exception as e:
                logger.error(f"Reservation creation error: {str(e)}")
                messages.error(request, "Error creating reservation.")
        
        context = {'lots': lots}
        return render(request, 'reserve_parking.html', context)
    except Exception as e:
        logger.error(f"Reserve parking error: {str(e)}")
        messages.error(request, "Error accessing reservations.")
        return redirect('dashboard')


@login_required
def my_reservations(request):
    """View user's reservations"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        reservations = ParkingReservation.objects.filter(user=user).order_by('-created_at')
        
        context = {
            'reservations': reservations,
            'active_count': reservations.filter(status='active').count(),
        }
        
        return render(request, 'my_reservations.html', context)
    except Exception as e:
        logger.error(f"My reservations error: {str(e)}")
        messages.error(request, "Error loading reservations.")
        return redirect('dashboard')


@login_required
def cancel_reservation(request, reservation_id):
    """Cancel a parking reservation"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        reservation = ParkingReservation.objects.get(reservation_id=reservation_id, user=user)
        
        if reservation.status == 'used':
            messages.error(request, "Cannot cancel a used reservation.")
            return redirect('my_reservations')
        
        reservation.status = 'cancelled'
        reservation.save()
        
        messages.success(request, "Reservation cancelled.")
        return redirect('my_reservations')
    except Exception as e:
        logger.error(f"Cancel reservation error: {str(e)}")
        messages.error(request, "Error cancelling reservation.")
        return redirect('my_reservations')


# ═══════════════════════════════════════════════════════════════════
# FEATURE 4: NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════

@login_required
def notifications(request):
    """View user notifications"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        notifications = UserNotification.objects.filter(user=user).order_by('-sent_at')
        unread_count = notifications.filter(is_read=False).count()
        
        context = {
            'notifications': notifications[:50],
            'unread_count': unread_count,
        }
        
        return render(request, 'notifications.html', context)
    except Exception as e:
        logger.error(f"Notifications error: {str(e)}")
        messages.error(request, "Error loading notifications.")
        return redirect('dashboard')


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        notification = UserNotification.objects.get(notification_id=notification_id, user=user)
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('notifications')
    except Exception as e:
        logger.error(f"Mark notification error: {str(e)}")
        return JsonResponse({'success': False}, status=400)


# ═══════════════════════════════════════════════════════════════════
# FEATURE 5: ANALYTICS & REPORTS (Admin)
# ═══════════════════════════════════════════════════════════════════

@login_required
def analytics_dashboard(request):
    """Admin analytics dashboard"""
    try:
        # Check if admin
        if not request.session.get('is_admin'):
            messages.error(request, "Access denied. Admin only.")
            return redirect('dashboard')
        
        # Overall statistics
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        
        total_sessions = ParkingSession.objects.count()
        today_sessions = ParkingSession.objects.filter(entry_time__date=today).count()
        month_revenue = ParkingSession.objects.filter(
            entry_time__date__gte=this_month_start
        ).aggregate(Sum('parking_fee'))['parking_fee__sum'] or 0
        
        # Lot statistics
        lot_stats = []
        for lot in ParkingLot.objects.all():
            analytics = lot.analytics.filter(date=today).first()
            lot_stats.append({
                'name': lot.lot_name,
                'total_spots': lot.total_spots,
                'available': lot.available_spots(),
                'occupancy_percent': ((lot.total_spots - lot.available_spots()) / lot.total_spots * 100) if lot.total_spots > 0 else 0,
                'today_sessions': today_sessions,
                'today_revenue': analytics.total_revenue if analytics else 0,
            })
        
        # Peak hours data (last 7 days)
        seven_days_ago = today - timedelta(days=7)
        daily_analytics = ParkingAnalytics.objects.filter(
            date__gte=seven_days_ago
        ).order_by('date')
        
        context = {
            'total_sessions': total_sessions,
            'today_sessions': today_sessions,
            'month_revenue': month_revenue,
            'lot_stats': lot_stats,
            'daily_analytics': daily_analytics,
        }
        
        return render(request, 'analytics_dashboard.html', context)
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        messages.error(request, "Error loading analytics.")
        return redirect('admin_dashboard')


@login_required
def revenue_report(request):
    """Detailed revenue report"""
    try:
        if not request.session.get('is_admin'):
            messages.error(request, "Access denied. Admin only.")
            return redirect('dashboard')
        
        # Revenue by time period
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        payments = Payment.objects.filter(
            created_at__date__gte=thirty_days_ago,
            payment_status='success'
        ).order_by('-created_at')
        
        # Summary
        total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        by_method = payments.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        context = {
            'payments': payments[:100],
            'total_revenue': total_revenue,
            'by_method': by_method,
            'thirty_days_ago': thirty_days_ago,
        }
        
        return render(request, 'revenue_report.html', context)
    except Exception as e:
        logger.error(f"Revenue report error: {str(e)}")
        messages.error(request, "Error loading revenue report.")
        return redirect('admin_dashboard')


# ═══════════════════════════════════════════════════════════════════
# API ENDPOINTS FOR REAL-TIME DATA
# ═══════════════════════════════════════════════════════════════════

def api_available_spots(request, lot_id):
    """Get available spots for a parking lot (JSON API)"""
    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
        data = {
            'lot_name': lot.lot_name,
            'total_spots': lot.total_spots,
            'available_spots': lot.available_spots(),
            'occupancy_percent': round(
                ((lot.total_spots - lot.available_spots()) / lot.total_spots * 100) if lot.total_spots > 0 else 0,
                2
            )
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"API available spots error: {str(e)}")
        return JsonResponse({'error': 'Parking lot not found'}, status=404)


def api_pricing(request, lot_id):
    """Get pricing information for a parking lot (JSON API)"""
    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
        pricing_rules = PricingRule.objects.filter(parking_lot=lot)
        
        data = {
            'lot_name': lot.lot_name,
            'pricing_rules': [
                {
                    'vehicle_type': rule.vehicle_type,
                    'base_rate': str(rule.base_rate),
                    'first_hour_free': rule.first_hour_free,
                    'max_daily_charge': str(rule.max_daily_charge) if rule.max_daily_charge else None,
                }
                for rule in pricing_rules
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"API pricing error: {str(e)}")
        return JsonResponse({'error': 'Parking lot not found'}, status=404)
