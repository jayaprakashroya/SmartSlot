import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()
from django.contrib.auth.models import User

print("=" * 60)
print("EXISTING USERS IN DATABASE")
print("=" * 60)

users = User.objects.all()

if not users.exists():
    print("\nNo users found in database!")
else:
    for user in users:
        print(f"\nUsername: {user.username}")
        print(f"Email: {user.email}")
        print(f"Type: {'ADMIN' if user.is_superuser else 'REGULAR USER'}")
    
    print("\n" + "=" * 60)
    print("LOGIN CREDENTIALS")
    print("=" * 60)
    
    for user in users:
        if user.is_superuser:
            print(f"\nADMIN:")
            print(f"  Username: {user.username}")
            print(f"  Password: AdminPass@123")
        else:
            print(f"\nREGULAR USER:")
            print(f"  Username: {user.username}")
            print(f"  Password: UserPass@123")

print("\n" + "=" * 60)
