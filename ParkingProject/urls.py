"""
URL configuration for ParkingProject project.
"""
from django.contrib import admin
from django.urls import path
from parkingapp import views as parking_views
from parkingapp import customer_views
from parkingapp import customer_views_enhanced
from parkingapp import admin_dashboard_views
from parkingapp import edge_case_views
from parkingapp import features_views
from parkingapp import advanced_features_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', parking_views.HomePage, name='home'),
    path('about/', parking_views.AboutPage, name='about'),
    path('contact/', parking_views.ContactPage, name='contact'),
    path('feedback/', parking_views.FeedbackPage, name='feedback'),
    path('login/', parking_views.LoginPage, name='login'),
    path('logout/', parking_views.LogoutPage, name='logout'),
    path('admin-login/', parking_views.AdminLoginPage, name='admin_login'),
    path('signup/', parking_views.SignupPage, name='signup'),
    path('dashboard/', parking_views.DashboardPage, name='dashboard'),
    path('detect-numberplate/', parking_views.detect_numberplate, name='detect_numberplate'),
    path('smart-car-parking/', parking_views.SmartParkingPage, name='smart_car_parking'),
    path('video/', parking_views.VideoPage, name='video'),
    
    # Customer-facing routes for parking spot tracking
    path('find-my-car/', customer_views.find_my_car, name='find_my_car'),
    path('parking-lot-status/', customer_views.parking_lot_status_all_lots, name='parking_lot_status'),
    path('parking-lot-status/<int:lot_id>/', customer_views.parking_lot_status, name='parking_lot_status_detail'),
    path('vehicle-history/', customer_views.vehicle_history, name='vehicle_history'),
    
    # API endpoints - Parking Management
    path('api/find-vehicle/', customer_views.api_find_vehicle, name='api_find_vehicle'),
    path('api/parking-status/', customer_views.api_parking_lot_status, name='api_parking_status'),
    path('api/parking-status/<int:lot_id>/', customer_views.api_parking_lot_status, name='api_parking_status_detail'),
    path('api/parking-statistics/<int:days>/', customer_views.api_parking_statistics, name='api_parking_statistics'),
    path('api/parking-statistics/<int:lot_id>/<int:days>/', customer_views.api_parking_statistics, name='api_parking_statistics_detail'),
    path('api/recent-activity/', customer_views.api_recent_activity, name='api_recent_activity'),
    path('api/recent-activity/<int:lot_id>/', customer_views.api_recent_activity, name='api_recent_activity_detail'),
    path('api/recent-activity/<int:lot_id>/<int:hours>/', customer_views.api_recent_activity, name='api_recent_activity_hours'),
    
    # YOLOv8 Integration API endpoints
    path('api/yolov8/webhook/', customer_views.yolov8_webhook, name='yolov8_webhook'),
    path('api/yolov8/process-image/', customer_views.process_image_detection, name='process_image_detection'),
    path('api/yolov8/detect-plate/', customer_views.detect_license_plate, name='detect_license_plate'),
    path('api/yolov8/status/', customer_views.yolov8_status, name='yolov8_status'),
    
    # Enhanced Real-Time Parking Tracking APIs
    path('api/parking/find-vehicle-realtime/', customer_views_enhanced.api_find_vehicle_realtime, name='api_find_vehicle_realtime'),
    path('api/parking/status-realtime/', customer_views_enhanced.api_parking_status_realtime, name='api_parking_status_realtime'),
    path('api/parking/update-spot/', customer_views_enhanced.api_update_parking_spot, name='api_update_parking_spot'),
    path('api/parking/remove-vehicle/', customer_views_enhanced.api_remove_vehicle, name='api_remove_vehicle'),
    
    # Enhanced Find My Car Page
    path('find-my-car-enhanced/', customer_views_enhanced.find_my_car_enhanced, name='find_my_car_enhanced'),
    
    # ========== Admin Dashboard - All 15 Scenarios ==========
    path('admin-dashboard/', admin_dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/disputes/', admin_dashboard_views.admin_dashboard_disputes, name='admin_dashboard_disputes'),
    path('api/admin/search-vehicle/', admin_dashboard_views.api_admin_search_vehicle, name='api_admin_search_vehicle'),
    path('api/admin/dashboard-stats/', admin_dashboard_views.api_admin_dashboard_stats, name='api_admin_dashboard_stats'),
    
    # ========== EDGE CASES & PROFESSIONAL SOLUTIONS ==========
    
    # 1. INTERNET OUTAGE - Offline Mode
    path('api/offline-status/', edge_case_views.offline_status, name='offline_status'),
    path('api/sync-pending-records/', edge_case_views.sync_pending_records, name='sync_pending_records'),
    path('offline-mode/', edge_case_views.pending_sync_queue_view, name='offline_mode'),
    
    # 2. DOUBLE PARKING & CONFIDENCE
    path('api/check-double-parking/', edge_case_views.check_double_parking, name='check_double_parking'),
    path('low-confidence-detections/', edge_case_views.low_confidence_detections, name='low_confidence_detections'),
    
    # 3. PRIVACY - PLATE MASKING
    path('plate-access-logs/', edge_case_views.plate_access_logs, name='plate_access_logs'),
    path('api/vehicle/<int:vehicle_id>/display/', edge_case_views.vehicle_display, name='vehicle_display'),
    
    # 4. DISPUTE HANDLING
    path('file-dispute/<int:parking_record_id>/', edge_case_views.file_dispute, name='file_dispute'),
    path('dispute/<int:dispute_id>/details/', edge_case_views.view_dispute_details, name='dispute_details'),
    path('api/dispute/<int:dispute_id>/resolve/', edge_case_views.resolve_dispute, name='resolve_dispute'),
    
    # 5. SEARCH WITHOUT PLATE - Multiple Methods
    path('search-by-phone/', edge_case_views.search_by_phone, name='search_by_phone'),
    path('api/search-by-ticket/', edge_case_views.search_by_ticket, name='search_by_ticket'),
    path('search-by-details/', edge_case_views.search_by_vehicle_details, name='search_by_vehicle_details'),
    path('api/parking-history/', edge_case_views.parking_history_api, name='parking_history_api'),
    
    # BONUS A: ADMIN FORCE RELEASE
    path('api/force-release-spot/<int:spot_id>/', edge_case_views.force_release_spot, name='force_release_spot'),
    path('api/manual-vehicle-entry/<int:spot_id>/', edge_case_views.manual_vehicle_entry, name='manual_vehicle_entry'),
    path('admin-action-history/', edge_case_views.admin_action_history, name='admin_action_history'),
    
    # BONUS B: HEATMAP - Real-Time Occupancy
    path('heatmap/', edge_case_views.parking_lot_heatmap, name='heatmap'),
    path('heatmap/<int:lot_id>/', edge_case_views.parking_lot_heatmap, name='heatmap_lot'),
    path('api/heatmap-analytics/<int:lot_id>/', edge_case_views.heatmap_analytics, name='heatmap_analytics'),
    path('api/heatmap-realtime/<int:lot_id>/', edge_case_views.heatmap_realtime_api, name='heatmap_realtime'),
    
    # ═══════════════════════════════════════════════════════════════════
    # NEW FEATURES: ADVANCED PARKING MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    # Feature 1: Parking History & Duration Tracking
    path('parking-history/', features_views.parking_history, name='parking_history'),
    path('end-parking-session/<int:session_id>/', features_views.end_parking_session, name='end_parking_session'),
    
    # Feature 2: Payment Processing
    path('payments/', features_views.payments, name='payments'),
    path('process-payment/<int:session_id>/', features_views.process_payment, name='process_payment'),
    
    # Feature 3: Parking Reservations
    path('reserve-parking/', features_views.reserve_parking, name='reserve_parking'),
    path('my-reservations/', features_views.my_reservations, name='my_reservations'),
    path('cancel-reservation/<int:reservation_id>/', features_views.cancel_reservation, name='cancel_reservation'),
    
    # Feature 4: Notifications
    path('notifications/', features_views.notifications, name='notifications'),
    path('mark-notification-read/<int:notification_id>/', features_views.mark_notification_read, name='mark_notification_read'),
    
    # Feature 5: Analytics & Reports (Admin)
    path('analytics-dashboard/', features_views.analytics_dashboard, name='analytics_dashboard'),
    path('revenue-report/', features_views.revenue_report, name='revenue_report'),
    
    # API Endpoints for Real-Time Data
    path('api/available-spots/<int:lot_id>/', features_views.api_available_spots, name='api_available_spots'),
    path('api/pricing/<int:lot_id>/', features_views.api_pricing, name='api_pricing'),
    
    # ═══════════════════════════════════════════════════════════════════
    # ADVANCED FEATURES: GPS, VEHICLE LOCATOR, DYNAMIC PRICING, etc.
    # ═══════════════════════════════════════════════════════════════════
    
    # GPS/Navigation Features
    path('parking-map/', advanced_features_views.parking_map, name='parking_map'),
    path('api/lot-directions/<int:lot_id>/', advanced_features_views.api_lot_directions, name='api_lot_directions'),
    
    # Lost Vehicle Locator
    path('find-my-vehicle/', advanced_features_views.find_my_vehicle, name='find_my_vehicle'),
    
    # Dynamic Pricing
    path('api/dynamic-pricing/<int:lot_id>/', advanced_features_views.dynamic_pricing_info, name='api_dynamic_pricing'),
    
    # Predictive Analytics
    path('peak-hours-forecast/', advanced_features_views.peak_hours_forecast, name='peak_hours_forecast'),
    
    # Accessibility Features
    path('accessible-parking/', advanced_features_views.accessible_parking, name='accessible_parking'),
    
    # Sensor Fault Reporting
    path('report-sensor-fault/', advanced_features_views.SensorFaultReport.report_sensor_fault, name='report_sensor_fault'),
    
    # Pricing Tiers - Passes
    path('purchase-pass/', advanced_features_views.purchase_pass, name='purchase_pass'),
    path('my-passes/', advanced_features_views.my_passes, name='my_passes'),
    
    # Staff Dashboard
    path('staff-dashboard/', advanced_features_views.staff_dashboard, name='staff_dashboard'),
    
    # Gate Control
    path('api/gate-control/<int:lot_id>/<str:action>/', advanced_features_views.api_gate_control, name='api_gate_control'),
    
    # Mobile PWA
    path('service-worker.js', advanced_features_views.service_worker, name='service_worker'),
    path('manifest.json', advanced_features_views.app_manifest, name='app_manifest'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
