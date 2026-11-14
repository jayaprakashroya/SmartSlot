#!/usr/bin/env python
"""
Test the AdminLoginPage view logic directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingProject.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test import RequestFactory

print("=" * 70)
print("SIMULATING ADMIN LOGIN VIEW LOGIC")
print("=" * 70)

# Simulate the login view logic
username_or_email = 'admin'
password = 'Admin@12345'

print(f"\nTesting login with:")
print(f"  Input: {username_or_email}")
print(f"  Password: {password}")

# Try Django authentication first with username
print("\n1. Attempting authentication with input as username...")
user = authenticate(username=username_or_email, password=password)

if user is None:
    print("   ✗ Failed - trying email lookup method")
    try:
        user_obj = User.objects.get(email=username_or_email)
        print(f"   ✓ Found user by email: {user_obj.username}")
        user = authenticate(username=user_obj.username, password=password)
        if user:
            print(f"   ✓ Authenticated with email lookup")
        else:
            print(f"   ✗ Authentication with email lookup failed")
    except User.DoesNotExist:
        print(f"   ✗ No user found with email: {username_or_email}")
else:
    print(f"   ✓ Authentication succeeded with username")

if user is not None:
    print(f"\n2. Checking admin status...")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    
    if user.is_staff or user.is_superuser:
        print(f"   ✓ User can access admin dashboard")
        print(f"\n✓ LOGIN WOULD SUCCEED")
    else:
        print(f"   ✗ User cannot access admin dashboard")
        print(f"\n✗ LOGIN WOULD FAIL: Access Denied message")
else:
    print(f"\n✗ LOGIN WOULD FAIL: Invalid credentials")

# Also test with email input
print("\n" + "=" * 70)
print("TESTING WITH EMAIL INPUT")
print("=" * 70)

username_or_email2 = 'admin@test.com'
print(f"\nTesting login with:")
print(f"  Input: {username_or_email2}")

user2 = authenticate(username=username_or_email2, password=password)
if user2 is None:
    print("1. ✗ Failed with email as username - trying email lookup")
    try:
        user_obj2 = User.objects.get(email=username_or_email2)
        print(f"2. ✓ Found user by email: {user_obj2.username}")
        user2 = authenticate(username=user_obj2.username, password=password)
        if user2:
            print(f"3. ✓ Authenticated with email lookup")
            print(f"\n✓ LOGIN WOULD SUCCEED with email")
        else:
            print(f"3. ✗ Authentication failed")
    except User.DoesNotExist:
        print(f"2. ✗ No user found with email: {username_or_email2}")
else:
    print(f"1. ✓ Authentication succeeded")

print("\n" + "=" * 70)
