"""
Role-Based Access Control (RBAC) System for Smart Parking
Manages user roles and permissions
"""
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.conf import settings
from functools import wraps


class RoleManager:
    """Manager for user roles and permissions"""
    
    ROLES = {
        'admin': 'Administrator - Full system access',
        'manager': 'Parking Manager - Manage parking operations',
        'attendant': 'Parking Attendant - Monitor parking',
        'user': 'Regular User - View and pay for parking'
    }
    
    PERMISSIONS = {
        'admin': [
            'view_all', 'manage_users', 'manage_payments', 'manage_parking',
            'view_analytics', 'manage_roles', 'view_system_logs', 'manage_settings'
        ],
        'manager': [
            'view_all', 'manage_parking', 'manage_payments', 'view_analytics'
        ],
        'attendant': [
            'view_parking', 'update_occupancy', 'view_lot_status'
        ],
        'user': [
            'view_parking', 'view_own_payments', 'make_payments'
        ]
    }
    
    @staticmethod
    def get_user_role(user):
        """Get user's role"""
        if not user.is_authenticated:
            return None
        
        if user.is_superuser or user.is_staff:
            return 'admin'
        
        # Get role from user profile or attribute
        if hasattr(user, 'profile'):
            return getattr(user.profile, 'role', 'user')
        if hasattr(user, 'role'):
            return user.role
        
        return 'user'
    
    @staticmethod
    def has_permission(user, permission):
        """Check if user has specific permission"""
        role = RoleManager.get_user_role(user)
        if role is None:
            return False
        
        permissions = RoleManager.PERMISSIONS.get(role, [])
        return permission in permissions
    
    @staticmethod
    def has_role(user, role):
        """Check if user has specific role"""
        user_role = RoleManager.get_user_role(user)
        return user_role == role
    
    @staticmethod
    def can_access_resource(user, resource_type):
        """Check if user can access specific resource type"""
        permission_map = {
            'admin_dashboard': 'view_all',
            'user_management': 'manage_users',
            'payment_management': 'manage_payments',
            'parking_management': 'manage_parking',
            'analytics': 'view_analytics',
            'parking_view': 'view_parking',
            'payments_view': 'view_own_payments'
        }
        
        required_permission = permission_map.get(resource_type)
        if not required_permission:
            return True
        
        return RoleManager.has_permission(user, required_permission)


def role_required(required_role):
    """Decorator to check if user has required role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")
            
            user_role = RoleManager.get_user_role(request.user)
            
            # Check if user has required role
            if isinstance(required_role, list):
                if user_role not in required_role:
                    return HttpResponseForbidden("You don't have permission to access this resource")
            else:
                if user_role != required_role:
                    return HttpResponseForbidden("You don't have permission to access this resource")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission):
    """Decorator to check if user has specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")
            
            if not RoleManager.has_permission(request.user, permission):
                return HttpResponseForbidden(f"Permission '{permission}' required")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleBasedAccessMiddleware:
    """Middleware for role-based access control"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add role information to request
        if request.user.is_authenticated:
            request.user_role = RoleManager.get_user_role(request.user)
            request.user_permissions = RoleManager.PERMISSIONS.get(request.user_role, [])
        else:
            request.user_role = None
            request.user_permissions = []
        
        response = self.get_response(request)
        return response


class AdminRequiredDecorator:
    """Custom decorator for admin-only access"""
    
    @staticmethod
    def admin_required(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect('login')
            
            user_role = RoleManager.get_user_role(request.user)
            if user_role != 'admin':
                return HttpResponseForbidden("Admin access required")
            
            return view_func(request, *args, **kwargs)
        return wrapper


class ManagerRequiredDecorator:
    """Custom decorator for manager-only access"""
    
    @staticmethod
    def manager_required(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect('login')
            
            user_role = RoleManager.get_user_role(request.user)
            if user_role not in ['admin', 'manager']:
                return HttpResponseForbidden("Manager access required")
            
            return view_func(request, *args, **kwargs)
        return wrapper


# Context processors for templates
def role_context(request):
    """Add role information to template context"""
    return {
        'user_role': RoleManager.get_user_role(request.user) if request.user.is_authenticated else None,
        'user_permissions': RoleManager.PERMISSIONS.get(
            RoleManager.get_user_role(request.user), []
        ) if request.user.is_authenticated else [],
        'all_roles': RoleManager.ROLES,
        'all_permissions': RoleManager.PERMISSIONS
    }
