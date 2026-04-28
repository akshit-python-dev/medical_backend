"""
Custom permissions for the clinic API.

Only doctors can access the frontend API.
Admins are handled through Django's admin interface (is_staff=True).
Patients cannot login.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsDoctorUser(IsAuthenticated):
    """
    Permission to check if user is a doctor accessing the API.
    - Doctors: is_staff=False, is_superuser=False, is_active=True
    - Admins: Use Django admin interface (not this API)
    """
    def has_permission(self, request, view):
        # Must be authenticated
        if not super().has_permission(request, view):
            return False
        
        # Must be a doctor (not staff/admin), must be active
        # Doctors are regular users, admins only access Django admin
        return not request.user.is_staff and request.user.is_active


class IsOwnDoctor(BasePermission):
    """
    Object-level permission to check if doctor is accessing their own data.
    Doctors can only view/modify their own patients and related records.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the object has a doctor field and it matches the request user
        if hasattr(obj, 'doctor'):
            return obj.doctor == request.user
        
        # For nested relationships (appointment -> patient -> doctor)
        if hasattr(obj, 'patient') and hasattr(obj.patient, 'doctor'):
            return obj.patient.doctor == request.user
        
        return False


class IsOwnDoctorQueryset(BasePermission):
    """
    QuerySet-level permission for list/create endpoints.
    Doctors only see their own patients and related data.
    """
    def has_permission(self, request, view):
        # All authenticated doctors can access
        return request.user and request.user.is_authenticated and not request.user.is_staff

