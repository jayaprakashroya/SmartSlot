#!/usr/bin/env python
"""
Diagnostic script to check admin user setup and login issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("=" * 70)
print("ADMIN LOGIN DIAGNOSTICS")
print("=" * 70)

# Check admin user
try:
    admin = User.objects.get(username='admin')
    print("\n✓ Admin user found:")
    print(f"  Username: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  is_active: {admin.is_active}")
    print(f"  is_staff: {admin.is_staff}")
    print(f"  is_superuser: {admin.is_superuser}")
    
    # Test authentication
    print("\n" + "=" * 70)
    print("AUTHENTICATION TEST")
    print("=" * 70)
    
    # Test with username
    admin_auth = authenticate(username='admin', password='Admin@12345')
    if admin_auth:
        print("✓ Authentication with username works")
        print(f"  User: {admin_auth.username}")
        print(f"  is_staff: {admin_auth.is_staff}")
        print(f"  is_superuser: {admin_auth.is_superuser}")
    else:
        print("✗ Authentication with username FAILED")
    
    # Test with email
    admin_auth_email = authenticate(username='admin@smartslot.com', password='Admin@12345')
    if admin_auth_email:
        print("\n✓ Authentication with email works")
    else:
        print("\n✗ Authentication with email FAILED - trying email lookup method")
        try:
            admin_by_email = User.objects.get(email='admin@smartslot.com')
            admin_auth_email2 = authenticate(username=admin_by_email.username, password='Admin@12345')
            if admin_auth_email2:
                print("✓ Email lookup method works")
            else:
                print("✗ Email lookup method FAILED")
        except User.DoesNotExist:
            print("✗ No user found with that email")
    
    # Check if user can access admin
    print("\n" + "=" * 70)
    print("ADMIN ACCESS CHECK")
    print("=" * 70)
    
    if admin.is_staff or admin.is_superuser:
        print("✓ Admin user can access admin panel (is_staff or is_superuser)")
    else:
        print("✗ Admin user CANNOT access admin panel - flags not set!")
        print("\n  Fixing admin flags...")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print("  ✓ Admin flags have been set")
        
        # Verify
        admin.refresh_from_db()
        print(f"  is_staff: {admin.is_staff}")
        print(f"  is_superuser: {admin.is_superuser}")
    
except User.DoesNotExist:
    print("✗ Admin user not found!")
    print("\n  Creating admin user...")
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@smartslot.com',
        password='Admin@12345'
    )
    print("✓ Admin user created successfully")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nAdmin should be able to login with:")
print("  Username/Email: admin")
print("  Password: Admin@12345")
print("\nLogin URL: http://localhost:8000/admin-login/")
print("\n" + "=" * 70)
