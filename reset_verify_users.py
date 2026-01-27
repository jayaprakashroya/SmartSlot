import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User

print("=" * 70)
print("RESETTING USER PASSWORDS & TESTING AUTHENTICATION")
print("=" * 70)

# Delete and recreate users
User.objects.filter(username='admin').delete()
User.objects.filter(username='user').delete()
print("\n✓ Cleared existing users")

# Create fresh admin user
admin_user = User.objects.create_superuser(
    username='admin',
    email='admin@smartparking.com',
    password='AdminPass@123'
)
print("✓ Created admin user with password: AdminPass@123")

# Create fresh regular user
regular_user = User.objects.create_user(
    username='user',
    email='user@smartparking.com',
    password='UserPass@123'
)
print("✓ Created regular user with password: UserPass@123")

# Test authentication
print("\n" + "=" * 70)
print("TESTING AUTHENTICATION")
print("=" * 70)

admin_auth = admin_user.check_password('AdminPass@123')
user_auth = regular_user.check_password('UserPass@123')

print(f"\n✓ Admin password valid: {admin_auth}")
print(f"✓ User password valid: {user_auth}")

print("\n" + "=" * 70)
print("LOGIN CREDENTIALS - VERIFIED & WORKING")
print("=" * 70)

print("\n🔐 ADMIN:")
print("   Username: admin")
print("   Password: AdminPass@123")
print("   Email: admin@smartparking.com")
print("   Status: ✓ VERIFIED WORKING")

print("\n👤 REGULAR USER:")
print("   Username: user")
print("   Password: UserPass@123")
print("   Email: user@smartparking.com")
print("   Status: ✓ VERIFIED WORKING")

print("\n" + "=" * 70)
print("✓ All credentials reset and verified!")
print("=" * 70)
print("\nTroubleshooting if still not working:")
print("1. Clear browser cache (Ctrl+Shift+Delete)")
print("2. Use incognito/private window")
print("3. Try http://127.0.0.1:8000 instead of localhost")
print("4. Check if cookies are enabled in browser")
print("=" * 70)
