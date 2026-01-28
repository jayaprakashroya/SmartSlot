from django.db import models
from django.utils import timezone

# Create your models here.

class User_details(models.Model):
    User_id = models.AutoField(primary_key = True)
    Email = models.EmailField(max_length = 50, unique=True)
    Password = models.CharField(max_length = 128, null = True)  # For hashed passwords

    class Meta:
        db_table = 'user_details'
    
    def __str__(self):
        return self.Email

class Upload_File(models.Model):
    Video_Id = models.AutoField(primary_key=True)
    Video = models.FileField(upload_to='videos/') 

    class Meta:
        db_table = 'upload_video'

class Contact_Message(models.Model):
    contact_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contact_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Contact from {self.name} - {self.subject}"

class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback'
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.username}"


# ═══════════════════════════════════════════════════════════════════
# NEW MODELS FOR PARKING SPOT & VEHICLE TRACKING
# ═══════════════════════════════════════════════════════════════════

class ParkingLot(models.Model):
    """Define parking lots"""
    lot_id = models.AutoField(primary_key=True)
    lot_name = models.CharField(max_length=100, unique=True)
    total_spots = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'parking_lot'
    
    def __str__(self):
        return f"{self.lot_name} ({self.total_spots} spots)"
    
    def available_spots(self):
        """Count available parking spots"""
        return self.total_spots - ParkedVehicle.objects.filter(
            parking_lot=self,
            checkout_time__isnull=True
        ).count()


class ParkingSpot(models.Model):
    """Individual parking spots"""
    spot_id = models.AutoField(primary_key=True)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spots')
    spot_number = models.CharField(max_length=10)  # A1, A2, B1, etc.
    spot_type = models.CharField(
        max_length=50,
        choices=[
            ('regular', 'Regular'),
            ('reserved', 'Reserved'),
            ('handicap', 'Handicap'),
            ('vip', 'VIP')
        ],
        default='regular'
    )
    x_position = models.IntegerField()  # X coordinate for video detection
    y_position = models.IntegerField()  # Y coordinate for video detection
    spot_width = models.IntegerField(default=107)   # Width of spot area
    spot_height = models.IntegerField(default=48)   # Height of spot area
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'parking_spot'
        unique_together = ('parking_lot', 'spot_number')
    
    def __str__(self):
        return f"{self.parking_lot.lot_name} - Spot {self.spot_number}"
    
    def is_occupied(self):
        """Check if spot is currently occupied"""
        return ParkedVehicle.objects.filter(
            parking_spot=self,
            checkout_time__isnull=True
        ).exists()
    
    def get_current_vehicle(self):
        """Get currently parked vehicle in this spot"""
        return ParkedVehicle.objects.filter(
            parking_spot=self,
            checkout_time__isnull=True
        ).first()


class Vehicle(models.Model):
    """Registered vehicles"""
    vehicle_id = models.AutoField(primary_key=True)
    license_plate = models.CharField(max_length=20, unique=True, db_index=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('car', 'Car'),
            ('truck', 'Truck'),
            ('motorcycle', 'Motorcycle'),
            ('bus', 'Bus'),
            ('unknown', 'Unknown')
        ],
        default='car'
    )
    owner_name = models.CharField(max_length=100, null=True, blank=True)
    owner_phone = models.CharField(max_length=15, null=True, blank=True)
    color = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vehicle'
    
    def __str__(self):
        return f"{self.license_plate} ({self.vehicle_type})"
    
    def is_parked(self):
        """Check if vehicle is currently parked"""
        return ParkedVehicle.objects.filter(
            vehicle=self,
            checkout_time__isnull=True
        ).exists()
    
    def get_parked_location(self):
        """Get current parking spot of this vehicle"""
        parked = ParkedVehicle.objects.filter(
            vehicle=self,
            checkout_time__isnull=True
        ).first()
        return parked.parking_spot if parked else None
    
    def get_parking_duration(self):
        """Get how long the vehicle has been parked"""
        parked = ParkedVehicle.objects.filter(
            vehicle=self,
            checkout_time__isnull=True
        ).first()
        if parked:
            return timezone.now() - parked.checkin_time
        return None


class ParkedVehicle(models.Model):
    """Track which vehicle is parked in which spot and when"""
    parking_record_id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='parking_history')
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    checkin_time = models.DateTimeField(auto_now_add=True, db_index=True)
    checkout_time = models.DateTimeField(null=True, blank=True)
    entry_image_path = models.FileField(upload_to='parking_images/entry/', null=True, blank=True)
    exit_image_path = models.FileField(upload_to='parking_images/exit/', null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    parking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('free', 'Free')
        ],
        default='pending'
    )
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'parked_vehicle'
        ordering = ['-checkin_time']
        indexes = [
            models.Index(fields=['vehicle', 'checkout_time']),
            models.Index(fields=['parking_spot', 'checkout_time']),
            models.Index(fields=['checkin_time']),
        ]
    
    def __str__(self):
        spot_info = f" in {self.parking_spot.spot_number}" if self.parking_spot else " (no spot assigned)"
        return f"{self.vehicle.license_plate}{spot_info} - {self.checkin_time.strftime('%Y-%m-%d %H:%M')}"
    
    def is_active(self):
        """Check if this parking session is still active"""
        return self.checkout_time is None
    
    def checkout(self):
        """Mark vehicle as checked out"""
        if self.is_active():
            self.checkout_time = timezone.now()
            duration = self.checkout_time - self.checkin_time
            self.duration_minutes = int(duration.total_seconds() / 60)
            self.save()
            return True
        return False
    
    def get_duration_display(self):
        """Get readable parking duration"""
        if self.is_active():
            duration = timezone.now() - self.checkin_time
        else:
            duration = self.checkout_time - self.checkin_time
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}h {minutes}m"


# ═══════════════════════════════════════════════════════════════════
# EDGE CASE HANDLING MODELS
# ═══════════════════════════════════════════════════════════════════

class PendingSyncQueue(models.Model):
    """Store records when internet is down - sync when connection returns"""
    sync_id = models.AutoField(primary_key=True)
    record_type = models.CharField(max_length=50)  # 'vehicle_entry', 'vehicle_exit', etc.
    vehicle_id = models.IntegerField(null=True)
    parking_spot_id = models.IntegerField(null=True)
    data = models.JSONField()  # Full record data in JSON
    synced = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'pending_sync_queue'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Pending Sync: {self.record_type} (ID: {self.sync_id})"


class DisputeLog(models.Model):
    """Handle customer disputes about parking records"""
    dispute_id = models.AutoField(primary_key=True)
    parked_vehicle = models.ForeignKey(ParkedVehicle, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    dispute_type = models.CharField(
        max_length=50,
        choices=[
            ('car_not_found', 'Car Not Found at Spot'),
            ('wrong_spot', 'Wrong Spot Assigned'),
            ('damage', 'Vehicle Damaged'),
            ('double_charge', 'Double Charged'),
            ('other', 'Other')
        ]
    )
    description = models.TextField()
    entry_image = models.FileField(upload_to='dispute_images/entry/', null=True, blank=True)
    entry_video = models.FileField(upload_to='dispute_videos/entry/', null=True, blank=True)
    detection_confidence = models.FloatField(default=0.95)
    
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending Review'),
            ('investigating', 'Under Investigation'),
            ('resolved_refund', 'Resolved - Refund Issued'),
            ('resolved_valid', 'Resolved - Record Valid'),
            ('rejected', 'Rejected'),
            ('escalated', 'Escalated to Management')
        ],
        default='pending'
    )
    admin_notes = models.TextField(null=True, blank=True)
    admin_decision = models.CharField(max_length=255, null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    handled_by = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'dispute_log'
        ordering = ['-reported_at']
    
    def __str__(self):
        return f"Dispute #{self.dispute_id}: {self.dispute_type} - {self.status}"


class AdminAction(models.Model):
    """Log all admin manual interventions"""
    action_id = models.AutoField(primary_key=True)
    admin_name = models.CharField(max_length=100)
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('force_release', 'Force Release Spot'),
            ('manual_entry', 'Manual Vehicle Entry'),
            ('manual_exit', 'Manual Vehicle Exit'),
            ('override_detection', 'Override Detection'),
            ('mark_double_parked', 'Mark as Double Parked'),
            ('resolve_dispute', 'Resolve Dispute'),
            ('camera_maintenance', 'Camera Maintenance')
        ]
    )
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField()
    notes = models.TextField(null=True, blank=True)
    before_state = models.JSONField(null=True, blank=True)  # State before action
    after_state = models.JSONField(null=True, blank=True)   # State after action
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_action'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Admin Action: {self.action_type} by {self.admin_name}"


class ParkingHistory(models.Model):
    """Customer parking history for easy retrieval"""
    history_id = models.AutoField(primary_key=True)
    phone_number = models.CharField(max_length=15, db_index=True)
    parked_vehicle = models.ForeignKey(ParkedVehicle, on_delete=models.CASCADE)
    ticket_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    ticket_qr = models.ImageField(upload_to='tickets/', null=True, blank=True)
    
    class Meta:
        db_table = 'parking_history'
        ordering = ['-parked_vehicle__checkin_time']
    
    def __str__(self):
        return f"History: {self.phone_number} - {self.parked_vehicle.vehicle.license_plate}"


class CameraStatus(models.Model):
    """Track camera health and availability"""
    camera_id = models.AutoField(primary_key=True)
    camera_name = models.CharField(max_length=100)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    spot_coverage = models.ManyToManyField(ParkingSpot, related_name='cameras')
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('maintenance', 'Maintenance'),
            ('error', 'Error')
        ],
        default='online',
        db_index=True
    )
    last_seen = models.DateTimeField(null=True, blank=True)
    last_check = models.DateTimeField(auto_now=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'camera_status'
    
    def __str__(self):
        return f"Camera: {self.camera_name} - {self.status}"
    
    def is_online(self):
        """Check if camera is currently online"""
        return self.status == 'online'


class DetectionLog(models.Model):
    """Log each detection for quality assurance"""
    detection_id = models.AutoField(primary_key=True)
    camera = models.ForeignKey(CameraStatus, on_delete=models.SET_NULL, null=True)
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    frame_image = models.ImageField(upload_to='detection_frames/')
    
    vehicles_detected = models.IntegerField()
    confidence_scores = models.JSONField()  # List of confidence scores
    
    license_plates = models.JSONField()  # Detected plates
    plate_confidence = models.JSONField()  # Plate recognition confidence
    
    manual_override = models.BooleanField(default=False)
    override_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'detection_log'
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"Detection on {self.detected_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.vehicles_detected} vehicles"


# ═══════════════════════════════════════════════════════════════════
# FEATURE 1: PARKING DURATION TRACKING & HISTORY
# ═══════════════════════════════════════════════════════════════════

class ParkingSession(models.Model):
    """Track user parking sessions"""
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User_details, on_delete=models.CASCADE, related_name='parking_sessions')
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='sessions')
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True)
    license_plate = models.CharField(max_length=20, null=True, blank=True)
    
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    parking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Unpaid'),
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled')
        ],
        default='unpaid'
    )
    
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('car', 'Car'),
            ('bike', 'Bike'),
            ('truck', 'Truck'),
            ('van', 'Van')
        ],
        default='car'
    )
    
    class Meta:
        db_table = 'parking_sessions'
        ordering = ['-entry_time']
    
    def __str__(self):
        return f"{self.user.Email} - {self.entry_time.strftime('%Y-%m-%d %H:%M')}"
    
    def calculate_duration(self):
        """Calculate parking duration in minutes"""
        if self.exit_time:
            delta = self.exit_time - self.entry_time
            return int(delta.total_seconds() / 60)
        else:
            delta = timezone.now() - self.entry_time
            return int(delta.total_seconds() / 60)


# ═══════════════════════════════════════════════════════════════════
# FEATURE 2: PAYMENT & BILLING SYSTEM
# ═══════════════════════════════════════════════════════════════════

class PricingRule(models.Model):
    """Dynamic pricing rules"""
    rule_id = models.AutoField(primary_key=True)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='pricing_rules')
    vehicle_type = models.CharField(max_length=20)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)  # $/hour
    first_hour_free = models.BooleanField(default=False)
    max_daily_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'pricing_rules'
    
    def __str__(self):
        return f"{self.parking_lot.lot_name} - {self.vehicle_type}: ${self.base_rate}/hour"


class Payment(models.Model):
    """Payment records"""
    payment_id = models.AutoField(primary_key=True)
    parking_session = models.OneToOneField(ParkingSession, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User_details, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('digital_wallet', 'Digital Wallet'),
            ('cash', 'Cash'),
            ('monthly_pass', 'Monthly Pass')
        ],
        default='credit_card'
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded')
        ],
        default='pending'
    )
    
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.payment_id} - ${self.amount}"


# ═══════════════════════════════════════════════════════════════════
# FEATURE 3: RESERVATION SYSTEM
# ═══════════════════════════════════════════════════════════════════

class ParkingReservation(models.Model):
    """Book parking spots in advance"""
    reservation_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User_details, on_delete=models.CASCADE, related_name='reservations')
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True)
    
    reserved_from = models.DateTimeField()
    reserved_until = models.DateTimeField()
    vehicle_type = models.CharField(max_length=20, default='car')
    license_plate = models.CharField(max_length=20, null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('used', 'Used'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired')
        ],
        default='active'
    )
    
    reservation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'parking_reservations'
        ordering = ['-created_at']
        unique_together = ('parking_spot', 'reserved_from', 'reserved_until')
    
    def __str__(self):
        return f"Reservation by {self.user.Email} - {self.reserved_from.strftime('%Y-%m-%d %H:%M')}"


# ═══════════════════════════════════════════════════════════════════
# FEATURE 4: NOTIFICATIONS SYSTEM
# ═══════════════════════════════════════════════════════════════════

class UserNotification(models.Model):
    """Send notifications to users"""
    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User_details, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('spot_available', 'Spot Available'),
            ('parking_expiring', 'Parking Expiring Soon'),
            ('payment_due', 'Payment Due'),
            ('reservation_reminder', 'Reservation Reminder'),
            ('parking_complete', 'Parking Complete'),
            ('promotion', 'Promotion'),
            ('general', 'General')
        ],
        default='general'
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Notification channels
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    in_app = models.BooleanField(default=True)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.Email}"


# ═══════════════════════════════════════════════════════════════════
# FEATURE 5: HISTORICAL DATA & ANALYTICS
# ═══════════════════════════════════════════════════════════════════

class ParkingAnalytics(models.Model):
    """Daily analytics for parking lots"""
    analytics_id = models.AutoField(primary_key=True)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='analytics')
    
    date = models.DateField()
    total_sessions = models.IntegerField(default=0)
    peak_occupancy_percent = models.IntegerField(default=0)  # 0-100%
    average_duration_minutes = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    peak_hour = models.IntegerField(null=True, blank=True)  # 0-23
    
    class Meta:
        db_table = 'parking_analytics'
        ordering = ['-date']
        unique_together = ('parking_lot', 'date')
    
    def __str__(self):
        return f"{self.parking_lot.lot_name} - {self.date}"


# ═══════════════════════════════════════════════════════════════════
# FEATURE 6: ADMIN SETTINGS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class ParkingLotSettings(models.Model):
    """Configuration for each parking lot"""
    settings_id = models.AutoField(primary_key=True)
    parking_lot = models.OneToOneField(ParkingLot, on_delete=models.CASCADE, related_name='settings')
    
    # GPS coordinates
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Operating hours
    opening_time = models.TimeField(default='08:00')
    closing_time = models.TimeField(default='22:00')
    
    # Features enabled
    enable_reservations = models.BooleanField(default=True)
    enable_dynamic_pricing = models.BooleanField(default=False)
    enable_notifications = models.BooleanField(default=True)
    
    # Pricing
    grace_period_minutes = models.IntegerField(default=15)  # Free parking period
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=2.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'parking_lot_settings'
    
    def __str__(self):
        return f"Settings for {self.parking_lot.lot_name}"


# ============ USER PROFILE & RBAC ============
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """User profile for role-based access control"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Parking Manager'),
        ('attendant', 'Parking Attendant'),
        ('user', 'Regular User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ============ PAYMENT SYSTEM ============
class Payment(models.Model):
    """Payment records for parking sessions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    invoice_id = models.CharField(max_length=20, unique=True)
    transaction_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='payments')
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='payments')
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    user_email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_id} - {self.amount} {self.currency} ({self.status})"