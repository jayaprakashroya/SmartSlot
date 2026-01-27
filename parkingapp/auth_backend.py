"""
Custom authentication backend to support login with both username and email
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate using either username or email
    """
    
    def authenticate(self, request, username=None, password=None):
        """
        Try to authenticate with username first, then email
        """
        try:
            # Try to authenticate with username
            user = super().authenticate(request, username=username, password=password)
            if user:
                return user
            
            # If username failed, try email
            user = User.objects.get(email=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            pass
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
