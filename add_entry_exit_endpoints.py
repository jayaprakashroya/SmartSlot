"""
Patch to add api_vehicle_checkin and api_vehicle_checkout to customer_views.py
Run with: python add_entry_exit_endpoints.py
"""

file_path = 'parkingapp/customer_views.py'

code_to_add = '''


@require_http_methods(["POST"])
def api_vehicle_checkin(request):
    """API: Vehicle entry with real timestamp"""
    try:
        data = json.loads(request.body)
        license_plate = data.get('license_plate', '').strip().upper()
        lot_id = data.get('lot_id')
        
        if not license_plate or not lot_id:
            return JsonResponse({'success': False, 'error': 'Missing fields'}, status=400)
        
        vehicle, _ = Vehicle.objects.get_or_create(
            license_plate=license_plate,
            defaults={'vehicle_type': 'car'}
        )
        lot = ParkingLot.objects.get(lot_id=lot_id)
        
        parked = ParkedVehicle.objects.create(
            vehicle=vehicle,
            parking_lot=lot,
            checkin_time=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'record_id': parked.parking_record_id,
            'checkin_time': parked.checkin_time.isoformat()
        })
    except Exception as e:
        logger.error(f'Checkin error: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def api_vehicle_checkout(request):
    """API: Vehicle exit with real timestamp"""
    try:
        data = json.loads(request.body)
        record_id = data.get('record_id')
        
        if not record_id:
            return JsonResponse({'success': False, 'error': 'Missing record_id'}, status=400)
        
        parked = ParkedVehicle.objects.get(parking_record_id=record_id)
        
        if parked.checkout_time:
            return JsonResponse({'success': False, 'error': 'Already checked out'}, status=400)
        
        parked.checkout_time = timezone.now()
        duration = parked.checkout_time - parked.checkin_time
        parked.duration_minutes = int(duration.total_seconds() / 60)
        parked.parking_fee = parked.calculate_fee()
        parked.save()
        
        return JsonResponse({
            'success': True,
            'checkout_time': parked.checkout_time.isoformat(),
            'duration_minutes': parked.duration_minutes,
            'parking_fee': float(parked.parking_fee)
        })
    except ParkedVehicle.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
    except Exception as e:
        logger.error(f'Checkout error: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
'''

with open(file_path, 'r') as f:
    content = f.read()

if 'api_vehicle_checkout' not in content:
    # Insert before the last few lines
    lines = content.split('\n')
    insert_pos = len(lines) - 1
    
    lines.insert(insert_pos, code_to_add)
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print('✅ Endpoints added successfully')
else:
    print('⚠️ Endpoints already exist')
