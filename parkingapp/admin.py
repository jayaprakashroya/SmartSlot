from django.contrib import admin
from parkingapp.models import (
    User_details, Upload_File, Contact_Message, Feedback,
    ParkingLot, ParkingSpot, Vehicle, ParkedVehicle
)

# Register your models here.

@admin.register(Contact_Message)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('contact_id', 'name', 'email', 'subject', 'created_at')
    list_filter = ('created_at', 'email')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedback_id', 'username', 'email', 'created_at')
    list_filter = ('created_at', 'email')
    search_fields = ('username', 'email', 'message')
    readonly_fields = ('created_at',)


# ═══════════════════════════════════════════════════════════════════
# NEW ADMIN CONFIGURATIONS FOR PARKING SPOT TRACKING
# ═══════════════════════════════════════════════════════════════════

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('lot_id', 'lot_name', 'total_spots', 'available_spots_display', 'created_at')
    search_fields = ('lot_name',)
    readonly_fields = ('created_at',)
    
    def available_spots_display(self, obj):
        """Display available spots count"""
        available = obj.available_spots()
        occupied = obj.total_spots - available
        return f"{available}/{obj.total_spots} available ({occupied} occupied)"
    available_spots_display.short_description = "Spot Status"


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ('spot_id', 'parking_lot', 'spot_number', 'spot_type', 'is_occupied_display', 'current_vehicle_display')
    list_filter = ('parking_lot', 'spot_type')
    search_fields = ('spot_number', 'parking_lot__lot_name')
    fieldsets = (
        ('Basic Info', {
            'fields': ('parking_lot', 'spot_number', 'spot_type')
        }),
        ('Video Detection Coordinates', {
            'fields': ('x_position', 'y_position', 'spot_width', 'spot_height'),
            'description': 'Coordinates and dimensions for automatic video detection'
        }),
    )
    readonly_fields = ('created_at',)
    
    def is_occupied_display(self, obj):
        """Show if spot is occupied"""
        if obj.is_occupied():
            return "🔴 Occupied"
        else:
            return "🟢 Available"
    is_occupied_display.short_description = "Status"
    
    def current_vehicle_display(self, obj):
        """Show current vehicle in spot"""
        vehicle = obj.get_current_vehicle()
        if vehicle:
            return vehicle.vehicle.license_plate
        return "—"
    current_vehicle_display.short_description = "Current Vehicle"


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_id', 'license_plate', 'vehicle_type', 'owner_name', 'is_parked_display', 'created_at')
    list_filter = ('vehicle_type', 'created_at')
    search_fields = ('license_plate', 'owner_name', 'owner_phone')
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('license_plate', 'vehicle_type', 'color')
        }),
        ('Owner Information', {
            'fields': ('owner_name', 'owner_phone')
        }),
    )
    readonly_fields = ('created_at',)
    
    def is_parked_display(self, obj):
        """Show if vehicle is currently parked"""
        if obj.is_parked():
            location = obj.get_parked_location()
            if location:
                return f"🟢 Parked at {location.spot_number}"
        return "⚪ Not Parked"
    is_parked_display.short_description = "Parking Status"


@admin.register(ParkedVehicle)
class ParkedVehicleAdmin(admin.ModelAdmin):
    list_display = ('parking_record_id', 'vehicle_display', 'parking_spot_display', 
                   'checkin_time', 'checkout_status', 'duration_display', 'payment_status')
    list_filter = ('parking_lot', 'payment_status', 'vehicle__vehicle_type', 'checkin_time')
    search_fields = ('vehicle__license_plate', 'vehicle__owner_name', 'parking_spot__spot_number')
    fieldsets = (
        ('Parking Session', {
            'fields': ('vehicle', 'parking_lot', 'parking_spot')
        }),
        ('Time Information', {
            'fields': ('checkin_time', 'checkout_time'),
            'classes': ('collapse',)
        }),
        ('Duration & Fee', {
            'fields': ('duration_minutes', 'parking_fee', 'payment_status'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('entry_image_path', 'exit_image_path'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('checkin_time', 'duration_minutes')
    
    def vehicle_display(self, obj):
        """Display vehicle with owner info"""
        owner = f" ({obj.vehicle.owner_name})" if obj.vehicle.owner_name else ""
        return f"{obj.vehicle.license_plate}{owner}"
    vehicle_display.short_description = "Vehicle"
    
    def parking_spot_display(self, obj):
        """Display parking spot info"""
        if obj.parking_spot:
            return f"{obj.parking_spot.parking_lot.lot_name} - {obj.parking_spot.spot_number}"
        return "Not assigned"
    parking_spot_display.short_description = "Location"
    
    def checkout_status(self, obj):
        """Show checkout status"""
        if obj.is_active():
            return "🟢 Still Parked"
        else:
            return f"⚪ Checked Out"
    checkout_status.short_description = "Status"
    
    def duration_display(self, obj):
        """Display parking duration"""
        return obj.get_duration_display()
    duration_display.short_description = "Duration"
    
    actions = ['checkout_vehicle']
    
    def checkout_vehicle(self, request, queryset):
        """Admin action to checkout vehicles"""
        count = 0
        for parked_vehicle in queryset.filter(checkout_time__isnull=True):
            parked_vehicle.checkout()
            count += 1
        
        self.message_user(request, f"✅ Checked out {count} vehicle(s).")
    checkout_vehicle.short_description = "Check out selected vehicles"

