#!/usr/bin/env python
"""
Fix: Mark all empty spots correctly - Make GREEN spots visible
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from parkingapp.models import ParkingLot, ParkingSpot, ParkedVehicle
from django.utils import timezone

print("=" * 70)
print("PARKING SPOT COLOR FIX - RESET ALL SPOTS TO EMPTY (GREEN)")
print("=" * 70)

# Get parking lots
lots = ParkingLot.objects.all()

if not lots.exists():
    print("❌ No parking lots found!")
    sys.exit(1)

total_cleared = 0

for lot in lots:
    print(f"\n🅿️  Processing lot: {lot.lot_name}")
    
    # Option 1: Clear all active parking (mark all spots as empty)
    if len(sys.argv) > 1 and sys.argv[1] == '--mark-all-empty':
        print("   Mode: Marking ALL spots as EMPTY (GREEN)")
        
        # Get all active parking sessions for this lot
        active_sessions = ParkedVehicle.objects.filter(
            parking_lot=lot,
            checkout_time__isnull=True
        )
        
        count = active_sessions.count()
        
        if count > 0:
            print(f"   Found {count} active sessions")
            print(f"   Clearing them... ", end='', flush=True)
            
            # Set checkout time to current time for all
            active_sessions.update(checkout_time=timezone.now())
            
            print("✅ Done")
            total_cleared += count
        else:
            print("   ✅ Already empty!")
    
    # Option 2: Verify consistency
    elif len(sys.argv) > 1 and sys.argv[1] == '--verify':
        print("   Mode: Verifying data consistency")
        
        spots = lot.spots.all()
        active = ParkedVehicle.objects.filter(
            parking_lot=lot,
            checkout_time__isnull=True
        ).count()
        
        occupied_count = sum(1 for s in spots if s.is_occupied())
        
        print(f"   Total spots: {spots.count()}")
        print(f"   Active records: {active}")
        print(f"   Occupied spots: {occupied_count}")
        
        if active == occupied_count:
            print("   ✅ Data is consistent")
        else:
            print("   ⚠️  Mismatch detected!")
            print(f"      → {active} active records but {occupied_count} occupied spots")
    
    # Default: Show current status
    else:
        spots = lot.spots.all()
        green_count = sum(1 for s in spots if not s.is_occupied())
        red_count = sum(1 for s in spots if s.is_occupied())
        
        print(f"   🟢 EMPTY (GREEN): {green_count}")
        print(f"   🔴 OCCUPIED (RED): {red_count}")
        print(f"   Total: {spots.count()}")
        
        if green_count == 0 and red_count > 0:
            print(f"   ⚠️  ALL spots showing RED - Run with --mark-all-empty to reset")

print("\n" + "=" * 70)
if len(sys.argv) > 1 and sys.argv[1] == '--mark-all-empty':
    print(f"✅ CLEARED {total_cleared} active parking sessions")
    print("   All spots are now EMPTY (will show GREEN)")
    print("   Spots will turn RED again when vehicles are detected")
else:
    print("Usage:")
    print("  python fix_parking_colors.py              # Show status")
    print("  python fix_parking_colors.py --verify     # Verify consistency")
    print("  python fix_parking_colors.py --mark-all-empty  # Clear all & show GREEN")
print("=" * 70)
