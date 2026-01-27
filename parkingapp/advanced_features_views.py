"""
Additional Missing Features for Smart Parking System
- GPS/Navigation & Map Display
- Lost Vehicle Locator
- Dynamic Pricing/Surge Pricing
- Predictive Analytics
- Queue Management
- Accessibility Features
- Sensor Fault Reporting
- Rate Tiers (Monthly/Daily/Hourly Passes)
- Gate Control Integration
- Mobile PWA
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
import json
import logging
import math

from parkingapp.models import (
    User_details, ParkingSession, ParkingReservation, 
    UserNotification, ParkingAnalytics, ParkingLot, 
    ParkingSpot, PricingRule, ParkingLotSettings
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# FEATURE: GPS/NAVIGATION & INTERACTIVE MAP
# ═══════════════════════════════════════════════════════════════════

@login_required
def parking_map(request):
    """Interactive map showing parking lots with directions"""
    try:
        lots = ParkingLot.objects.all()
        
        # Prepare lot data for map
        lot_data = []
        for lot in lots:
            settings = lot.settings
            lot_data.append({
                'id': lot.lot_id,
                'name': lot.lot_name,
                'latitude': settings.latitude if settings else 0,
                'longitude': settings.longitude if settings else 0,
                'address': settings.address if settings else 'Address not available',
                'phone': settings.phone if settings else '',
                'available_spots': lot.available_spots(),
                'total_spots': lot.total_spots,
                'occupancy_percent': round(
                    ((lot.total_spots - lot.available_spots()) / lot.total_spots * 100) 
                    if lot.total_spots > 0 else 0, 1
                ),
                'distance': 0  # Will be calculated on frontend
            })
        
        context = {
            'lots': lots,
            'lot_data': json.dumps(lot_data),
        }
        
        return render(request, 'parking_map.html', context)
    except Exception as e:
        logger.error(f"Parking map error: {str(e)}")
        messages.error(request, "Error loading map.")
        return redirect('dashboard')


def api_lot_directions(request, lot_id):
    """Get directions to a parking lot (integrate with Google Maps API)"""
    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
        settings = lot.settings
        
        data = {
            'lot_id': lot.lot_id,
            'name': lot.lot_name,
            'address': settings.address if settings else 'Address not available',
            'latitude': settings.latitude if settings else 0,
            'longitude': settings.longitude if settings else 0,
            'phone': settings.phone if settings else '',
            'available_spots': lot.available_spots(),
            'total_spots': lot.total_spots,
            'directions_url': f'https://maps.google.com/maps?q={settings.latitude},{settings.longitude}' if settings and settings.latitude else ''
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"API directions error: {str(e)}")
        return JsonResponse({'error': 'Lot not found'}, status=404)


# ═══════════════════════════════════════════════════════════════════
# FEATURE: LOST VEHICLE LOCATOR
# ═══════════════════════════════════════════════════════════════════

@login_required
def find_my_vehicle(request):
    """Help user find their parked vehicle"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        
        # Find active parking session
        active_session = ParkingSession.objects.filter(
            user=user,
            exit_time__isnull=True
        ).first()
        
        # Find recent sessions (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_sessions = ParkingSession.objects.filter(
            user=user,
            entry_time__gte=seven_days_ago
        ).order_by('-entry_time')
        
        context = {
            'active_session': active_session,
            'recent_sessions': recent_sessions,
        }
        
        return render(request, 'find_my_vehicle.html', context)
    except Exception as e:
        logger.error(f"Find vehicle error: {str(e)}")
        messages.error(request, "Error finding vehicle.")
        return redirect('dashboard')


# ═══════════════════════════════════════════════════════════════════
# FEATURE: DYNAMIC PRICING / SURGE PRICING
# ═══════════════════════════════════════════════════════════════════

def calculate_dynamic_price(parking_lot, occupancy_percent):
    """Calculate dynamic price based on occupancy (surge pricing)"""
    base_pricing = PricingRule.objects.filter(parking_lot=parking_lot).first()
    
    if not base_pricing:
        return base_pricing.base_rate if base_pricing else 2.50
    
    base_rate = float(base_pricing.base_rate)
    
    # Surge pricing formula
    # 0-30% occupancy: base rate
    # 30-60%: base rate * 1.2
    # 60-85%: base rate * 1.5
    # 85%+: base rate * 2.0
    
    if occupancy_percent >= 85:
        return base_rate * 2.0
    elif occupancy_percent >= 60:
        return base_rate * 1.5
    elif occupancy_percent >= 30:
        return base_rate * 1.2
    else:
        return base_rate


@login_required
def dynamic_pricing_info(request, lot_id):
    """Show dynamic pricing information for a lot"""
    try:
        lot = ParkingLot.objects.get(lot_id=lot_id)
        occupancy = ((lot.total_spots - lot.available_spots()) / lot.total_spots * 100) if lot.total_spots > 0 else 0
        
        current_price = calculate_dynamic_price(lot, occupancy)
        
        data = {
            'lot_name': lot.lot_name,
            'occupancy_percent': round(occupancy, 1),
            'available_spots': lot.available_spots(),
            'total_spots': lot.total_spots,
            'base_rate': str(float(PricingRule.objects.filter(parking_lot=lot).first().base_rate) if PricingRule.objects.filter(parking_lot=lot).exists() else 2.50),
            'current_dynamic_rate': str(round(current_price, 2)),
            'surge_multiplier': round(current_price / (float(PricingRule.objects.filter(parking_lot=lot).first().base_rate) if PricingRule.objects.filter(parking_lot=lot).exists() else 2.50), 2),
            'pricing_tiers': {
                '0-30%': '1.0x (Base rate)',
                '30-60%': '1.2x (20% surge)',
                '60-85%': '1.5x (50% surge)',
                '85%+': '2.0x (100% surge - Peak hours)'
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Dynamic pricing error: {str(e)}")
        return JsonResponse({'error': 'Lot not found'}, status=404)


# ═══════════════════════════════════════════════════════════════════
# FEATURE: PREDICTIVE ANALYTICS - PEAK HOURS
# ═══════════════════════════════════════════════════════════════════

@login_required
def peak_hours_forecast(request):
    """Predict peak hours and busy times"""
    try:
        if not request.session.get('is_admin'):
            messages.error(request, "Admin only.")
            return redirect('dashboard')
        
        # Analyze last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        analytics = ParkingAnalytics.objects.filter(
            date__gte=thirty_days_ago
        ).order_by('date')
        
        # Group by hour of day
        hourly_data = {}
        for i in range(24):
            hourly_data[i] = {'sessions': 0, 'occupancy': 0, 'count': 0}
        
        # Aggregate data
        for record in analytics:
            if record.peak_hour:
                hour = record.peak_hour
                hourly_data[hour]['sessions'] += record.total_sessions
                hourly_data[hour]['occupancy'] += record.peak_occupancy_percent
                hourly_data[hour]['count'] += 1
        
        # Calculate averages and predictions
        forecast = []
        for hour in range(24):
            if hourly_data[hour]['count'] > 0:
                avg_occupancy = hourly_data[hour]['occupancy'] / hourly_data[hour]['count']
                forecast.append({
                    'hour': f"{hour:02d}:00",
                    'occupancy_percent': round(avg_occupancy, 1),
                    'expected_sessions': hourly_data[hour]['sessions'] // max(1, hourly_data[hour]['count']),
                    'is_peak': avg_occupancy > 70,
                    'recommendation': 'Avoid peak hours' if avg_occupancy > 70 else 'Good availability'
                })
        
        context = {
            'forecast': forecast,
            'peak_hours': [h for h in forecast if h['is_peak']],
        }
        
        return render(request, 'peak_hours_forecast.html', context)
    except Exception as e:
        logger.error(f"Peak hours error: {str(e)}")
        messages.error(request, "Error loading forecast.")
        return redirect('admin_dashboard')


# ═══════════════════════════════════════════════════════════════════
# FEATURE: QUEUE MANAGEMENT - WAITING LIST
# ═══════════════════════════════════════════════════════════════════

class ParkingWaitlist:
    """Track users waiting for parking spots"""
    
    @staticmethod
    @login_required
    def join_waitlist(request, lot_id):
        """Join waiting list for a parking lot"""
        try:
            user = User_details.objects.get(Email=request.session.get('user_email'))
            lot = ParkingLot.objects.get(lot_id=lot_id)
            
            # Check if already on waitlist
            # Store in session for demo (in production: create WaitlistEntry model)
            if 'waitlist' not in request.session:
                request.session['waitlist'] = {}
            
            if lot_id not in request.session['waitlist']:
                request.session['waitlist'][lot_id] = {
                    'joined_at': timezone.now().isoformat(),
                    'position': 1
                }
                request.session.modified = True
                
                messages.success(request, f"You've been added to waitlist for {lot.lot_name}")
            
            return redirect('parking_map')
        except Exception as e:
            logger.error(f"Waitlist error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════
# FEATURE: ACCESSIBILITY - HANDICAP SPOTS
# ═══════════════════════════════════════════════════════════════════

@login_required
def accessible_parking(request):
    """Show accessible/handicap parking spots"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        
        # Get all accessible spots
        accessible_lots = []
        for lot in ParkingLot.objects.all():
            accessible_spots = lot.spots.filter(spot_type='handicap')
            if accessible_spots.exists():
                available_accessible = accessible_spots.filter(
                    Q(parked_vehicles__checkout_time__isnull=False) | 
                    Q(parked_vehicles__isnull=True)
                ).distinct().count()
                
                accessible_lots.append({
                    'lot': lot,
                    'total_accessible': accessible_spots.count(),
                    'available_accessible': available_accessible,
                })
        
        context = {
            'accessible_lots': accessible_lots,
        }
        
        return render(request, 'accessible_parking.html', context)
    except Exception as e:
        logger.error(f"Accessible parking error: {str(e)}")
        messages.error(request, "Error loading accessible spots.")
        return redirect('dashboard')


# ═══════════════════════════════════════════════════════════════════
# FEATURE: SENSOR FAULT REPORTING
# ═══════════════════════════════════════════════════════════════════

class SensorFaultReport:
    """Report broken/malfunctioning sensors"""
    
    @staticmethod
    @login_required
    def report_sensor_fault(request):
        """Report broken sensor in parking lot"""
        if request.method == 'POST':
            try:
                lot_id = request.POST.get('parking_lot')
                spot_number = request.POST.get('spot_number')
                description = request.POST.get('description')
                
                # In production: create SensorFault model
                # For demo: create notification to admin
                
                user = User_details.objects.get(Email=request.session.get('user_email'))
                
                # Create admin notification
                UserNotification.objects.create(
                    user_id=1,  # Admin user
                    notification_type='general',
                    title='Sensor Fault Report',
                    message=f'User {user.Email} reported faulty sensor at spot {spot_number} in lot {lot_id}: {description}'
                )
                
                messages.success(request, "Fault reported. Our team will investigate.")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Sensor fault report error: {str(e)}")
                messages.error(request, "Error reporting fault.")
                return redirect('dashboard')
        
        lots = ParkingLot.objects.all()
        return render(request, 'report_sensor_fault.html', {'lots': lots})


# ═══════════════════════════════════════════════════════════════════
# FEATURE: PRICING TIERS - Monthly/Daily/Hourly Passes
# ═══════════════════════════════════════════════════════════════════

@login_required
def purchase_pass(request):
    """Purchase parking passes (monthly, daily, hourly)"""
    try:
        user = User_details.objects.get(Email=request.session.get('user_email'))
        lots = ParkingLot.objects.all()
        
        # Define pass types and pricing
        pass_types = [
            {
                'id': 'hourly',
                'name': 'Hourly Pass',
                'price': 2.50,
                'duration_hours': 1,
                'benefits': ['Valid for 1 hour', 'Any parking lot', 'Flexible timing']
            },
            {
                'id': 'daily',
                'name': 'Daily Pass',
                'price': 15.00,
                'duration_hours': 24,
                'benefits': ['Valid for 24 hours', 'Unlimited entries', 'Any parking lot', '40% savings vs hourly']
            },
            {
                'id': 'weekly',
                'name': 'Weekly Pass',
                'price': 80.00,
                'duration_hours': 168,
                'benefits': ['Valid for 7 days', 'Unlimited entries', 'All parking lots', '50% savings vs hourly']
            },
            {
                'id': 'monthly',
                'name': 'Monthly Pass',
                'price': 250.00,
                'duration_hours': 720,
                'benefits': ['Valid for 30 days', 'Unlimited entries', 'Priority spots', '60% savings vs hourly']
            }
        ]
        
        if request.method == 'POST':
            pass_type = request.POST.get('pass_type')
            lot_id = request.POST.get('parking_lot')
            
            # Find pass details
            pass_details = next((p for p in pass_types if p['id'] == pass_type), None)
            if not pass_details:
                messages.error(request, "Invalid pass type.")
                return render(request, 'purchase_pass.html', {'pass_types': pass_types, 'lots': lots})
            
            # Create purchase record
            # In production: integrate with payment gateway
            # For demo: store in session
            
            if 'passes' not in request.session:
                request.session['passes'] = []
            
            pass_record = {
                'type': pass_type,
                'lot_id': lot_id,
                'purchased_at': timezone.now().isoformat(),
                'valid_until': (timezone.now() + timedelta(hours=pass_details['duration_hours'])).isoformat(),
                'price': pass_details['price']
            }
            
            request.session['passes'].append(pass_record)
            request.session.modified = True
            
            messages.success(request, f"{pass_details['name']} purchased successfully! Valid until {pass_record['valid_until']}")
            return redirect('parking_history')
        
        context = {
            'pass_types': pass_types,
            'lots': lots,
        }
        
        return render(request, 'purchase_pass.html', context)
    except Exception as e:
        logger.error(f"Purchase pass error: {str(e)}")
        messages.error(request, "Error purchasing pass.")
        return redirect('dashboard')


@login_required
def my_passes(request):
    """View active parking passes"""
    try:
        passes = request.session.get('passes', [])
        
        # Filter active passes
        active_passes = []
        for pass_record in passes:
            valid_until = datetime.fromisoformat(pass_record['valid_until'])
            if valid_until > timezone.now():
                active_passes.append(pass_record)
        
        context = {
            'active_passes': active_passes,
            'expired_passes': len(passes) - len(active_passes),
        }
        
        return render(request, 'my_passes.html', context)
    except Exception as e:
        logger.error(f"My passes error: {str(e)}")
        messages.error(request, "Error loading passes.")
        return redirect('dashboard')


# ═══════════════════════════════════════════════════════════════════
# FEATURE: STAFF DASHBOARD - Issue Management
# ═══════════════════════════════════════════════════════════════════

@login_required
def staff_dashboard(request):
    """Staff/attendant dashboard for managing parking lot issues"""
    try:
        if not request.session.get('is_staff'):
            messages.error(request, "Staff only.")
            return redirect('dashboard')
        
        # Get pending issues/faults
        # In production: query from proper Issue/Fault models
        
        context = {
            'pending_issues': [],
            'reported_faults': [],
            'recent_incidents': [],
        }
        
        return render(request, 'staff_dashboard.html', context)
    except Exception as e:
        logger.error(f"Staff dashboard error: {str(e)}")
        messages.error(request, "Error loading staff dashboard.")
        return redirect('dashboard')


# ═══════════════════════════════════════════════════════════════════
# FEATURE: GATE CONTROL INTEGRATION (Placeholder)
# ═══════════════════════════════════════════════════════════════════

def api_gate_control(request, lot_id, action):
    """Control parking lot gate (open/close) - requires hardware integration"""
    try:
        if action not in ['open', 'close', 'status']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # In production: integrate with:
        # - ALPR (Automatic License Plate Recognition) system
        # - Gate control hardware (boom barriers, sliding gates, etc.)
        # - Vehicle detection sensors
        
        lot = ParkingLot.objects.get(lot_id=lot_id)
        
        data = {
            'lot_id': lot_id,
            'lot_name': lot.lot_name,
            'action': action,
            'status': 'closed',
            'message': 'Gate control integration pending hardware setup',
            'integration_required': [
                'ALPR System',
                'Gate Hardware Controller',
                'Vehicle Detection Sensors',
                'Access Control System'
            ]
        }
        
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Gate control error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════
# FEATURE: MOBILE PWA (Progressive Web App)
# ═══════════════════════════════════════════════════════════════════

def service_worker(request):
    """Service worker for offline functionality and caching"""
    return render(request, 'service_worker.js', content_type='application/javascript')


def app_manifest(request):
    """Web app manifest for PWA"""
    manifest = {
        'name': 'SmartSlot - Smart Parking',
        'short_name': 'SmartSlot',
        'description': 'Real-time parking management and spot finder',
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#007bff',
        'orientation': 'portrait-primary',
        'icons': [
            {
                'src': '/static/icon-192x192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any'
            },
            {
                'src': '/static/icon-512x512.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any'
            }
        ]
    }
    return JsonResponse(manifest)
