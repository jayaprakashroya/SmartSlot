import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User

# Create superuser if doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'Admin@12345')
    print("✓ Superuser 'admin' created with password 'Admin@12345'")
else:
    print("✓ Superuser 'admin' already exists")
