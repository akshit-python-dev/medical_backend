"""
Admin configuration for the clinic app.
Only admins (is_staff=True) can access Django admin.
Doctors use the frontend API only.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Patient, Appointment, MedicalRecord, MedicalReport,
    Prescription, Billing, ClinicStats
)

User = get_user_model()


@admin.register(User)
class DoctorAdmin(BaseUserAdmin):
    """Admin interface for managing doctors."""
    list_display = ('username', 'get_full_name', 'email', 'phone', 'specialization', 'date_joined')
    list_filter = ('date_joined', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'specialization')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Medical Info', {'fields': ('phone', 'specialization')}),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    get_full_name.short_description = 'Doctor Name'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for managing patients."""
    list_display = ('get_full_name', 'doctor', 'email', 'phone', 'gender', 'created_at')
    list_filter = ('gender', 'doctor', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'doctor__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {'fields': ('doctor', 'first_name', 'last_name', 'email', 'phone')}),
        ('Medical Info', {'fields': ('date_of_birth', 'gender', 'address', 'medical_history')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Patient Name'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for managing appointments."""
    list_display = ('get_patient_name', 'doctor', 'appointment_date', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__username', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Appointment Details', {'fields': ('patient', 'doctor', 'appointment_date', 'status')}),
        ('Notes', {'fields': ('reason', 'notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    get_patient_name.short_description = 'Patient'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """Admin interface for managing medical records."""
    list_display = ('get_patient_name', 'doctor', 'get_appointment_date', 'follow_up_date', 'created_at')
    list_filter = ('doctor', 'created_at', 'follow_up_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'diagnosis', 'doctor__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Patient & Doctor', {'fields': ('patient', 'doctor', 'appointment')}),
        ('Medical Details', {'fields': ('diagnosis', 'treatment', 'medications', 'vital_signs')}),
        ('Follow-up', {'fields': ('follow_up_date',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    get_patient_name.short_description = 'Patient'
    
    def get_appointment_date(self, obj):
        return obj.appointment.appointment_date if obj.appointment else '-'
    get_appointment_date.short_description = 'Appointment Date'


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    """Admin interface for managing medical reports."""
    list_display = ('get_patient_name', 'get_report_type_display', 'title', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'title', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Patient', {'fields': ('patient',)}),
        ('Report Details', {'fields': ('report_type', 'title', 'file', 'description')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    get_patient_name.short_description = 'Patient'


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin interface for managing prescriptions."""
    list_display = ('medication_name', 'get_patient_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('medication_name', 'medical_record__patient__first_name', 'medical_record__patient__last_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Medical Record', {'fields': ('medical_record',)}),
        ('Medication', {'fields': ('medication_name',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    
    def get_patient_name(self, obj):
        return f"{obj.medical_record.patient.first_name} {obj.medical_record.patient.last_name}"
    get_patient_name.short_description = 'Patient'


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    """Admin interface for managing billing/invoices."""
    list_display = ('id', 'get_patient_name', 'amount', 'status', 'invoice_date', 'due_date')
    list_filter = ('status', 'invoice_date', 'due_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'invoice_date')
    
    fieldsets = (
        ('Patient & Appointment', {'fields': ('patient', 'appointment')}),
        ('Billing Info', {'fields': ('amount', 'status', 'description')}),
        ('Dates', {'fields': ('invoice_date', 'due_date', 'payment_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    get_patient_name.short_description = 'Patient'


@admin.register(ClinicStats)
class ClinicStatsAdmin(admin.ModelAdmin):
    """Admin interface for viewing clinic statistics."""
    list_display = ('date', 'total_patients', 'total_appointments', 'completed_appointments', 'total_revenue')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_patients', 'total_appointments', 'completed_appointments', 
                       'pending_bills', 'total_revenue', 'updated_at')
    
    fieldsets = (
        ('Statistics', {
            'fields': ('date', 'total_patients', 'total_appointments', 'completed_appointments', 
                      'pending_bills', 'total_revenue', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
