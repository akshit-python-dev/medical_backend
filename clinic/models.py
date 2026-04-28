"""
Models for the clinic management system.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator


class User(AbstractUser):
    """
    Custom doctor user model for the clinic system.
    Only doctors can login to the frontend platform via API.
    Admins access Django admin dashboard separately (using is_staff, is_superuser).
    """
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=200)
    
    def __str__(self):
        return f"Dr. {self.get_full_name() or self.username}"
    
    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'


class Patient(models.Model):
    """Patient model with medical history."""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patients')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['doctor']),
        ]
        unique_together = ('doctor', 'email')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    """Appointment scheduling model."""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date']
        indexes = [
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Appointment - {self.patient.first_name} on {self.appointment_date}"


class MedicalRecord(models.Model):
    """Medical records and consultation notes."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_records')
    diagnosis = models.TextField()
    treatment = models.TextField()
    medications = models.TextField()
    vital_signs = models.JSONField(default=dict, blank=True)  # BP, temp, etc
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Medical Records"
    
    def __str__(self):
        return f"Medical Record - {self.patient.first_name}"


class MedicalReport(models.Model):
    """File uploads for medical reports."""
    REPORT_TYPE_CHOICES = [
        ('lab_test', 'Lab Test'),
        ('xray', 'X-Ray'),
        ('ultrasound', 'Ultrasound'),
        ('ct_scan', 'CT Scan'),
        ('prescription', 'Prescription'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='medical_reports/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])]
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.patient.first_name}"


class Prescription(models.Model):
    """Prescription model."""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)  # e.g., "Twice daily"
    duration = models.CharField(max_length=100)  # e.g., "7 days"
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medication_name} - {self.dosage}"


class Billing(models.Model):
    """Billing and invoice model."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField()
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.patient.first_name}"


class ClinicStats(models.Model):
    """Dashboard statistics model."""
    date = models.DateField(auto_now_add=True, unique=True)
    total_patients = models.IntegerField(default=0)
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    pending_bills = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Clinic Stats"
    
    def __str__(self):
        return f"Stats - {self.date}"
