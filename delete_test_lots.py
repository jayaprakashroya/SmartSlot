"""One-off script to remove parking lots containing the word 'test'.
Run with: python delete_test_lots.py
This prevents the 'Test Lot' entry from showing up in the dashboard.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
import django
django.setup()

from parkingapp.models import ParkingLot

def main():
    to_delete = ParkingLot.objects.filter(lot_name__icontains='test')
    if not to_delete.exists():
        print('No test lots found.')
        return
    for lot in to_delete:
        print(f'Deleting lot: {lot.lot_name} (id={lot.lot_id})')
        lot.delete()
    print('Test lots removed.')

if __name__ == '__main__':
    main()
