from rest_framework import permissions
from django.conf import settings

class HasFaceEngineAPIKey(permissions.BasePermission):
    """
    Custom permission for the Face Recognition Engine to authenticate
    using a static API Key.
    """
    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return False
            
        parts = auth_header.split()
        if len(parts) == 2 and parts[0] == 'Api-Key':
            api_key = parts[1]
            # Ensure the API key is configured in settings and matches
            if settings.FACE_ENGINE_API_KEY and api_key == settings.FACE_ENGINE_API_KEY:
                return True
        return False
