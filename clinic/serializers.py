"""
Serializers for the clinic API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Patient, Appointment, MedicalRecord, MedicalReport,
    Prescription, Billing, ClinicStats
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Doctor registration and profile."""
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'phone', 'specialization', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True},
            'specialization': {'required': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'father_name', 'age', 'gender', 'address',
            'medical_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_age(self, obj):
        from datetime import date
        today = date.today()
        return today.year - obj.date_of_birth.year - (
            (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
        )


class PrescriptionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(source='medical_record.patient', read_only=True)
    class Meta:
        model = Prescription
        fields = [
            'id', 'medication_name', 'dosage', 'frequency', 'patient',
            'duration', 'instructions', 'created_at'
        ]
        read_only_fields = ['created_at']
    


class MedicalRecordSerializer(serializers.ModelSerializer):
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'patient', 'appointment', 'doctor', 'diagnosis', 'treatment',
            'medications', 'vital_signs', 'doctor_name', 'follow_up_date',
            'prescriptions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'doctor_name','doctor']


class MedicalReportSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        source='patient',
        queryset=Patient.objects.all(),
        write_only=True,
        required=False
    )

    
    class Meta:
        model = MedicalReport
        fields = [
            'id', 'patient', 'patient_id', 'report_type', 'title', 'file',
            'file_url', 'description', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        source='patient',
        queryset=Patient.objects.all(),
        write_only=True,
        required=False
    )
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_id', 'patient_name', 'doctor', 'doctor_name',
            'appointment_date', 'status', 'reason', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'doctor_name', 'doctor']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class BillingSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        source='patient',
        queryset=Patient.objects.all(),
        write_only=True,
        required=False
    )
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Billing
        fields = [
            'id', 'patient', 'patient_id', 'patient_name', 'appointment',
            'amount', 'status', 'description', 'invoice_date',
            'due_date', 'payment_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'invoice_date']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class ClinicStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicStats
        fields = [
            'id', 'date', 'total_patients', 'total_appointments',
            'completed_appointments', 'pending_bills', 'total_revenue',
            'updated_at'
        ]
        read_only_fields = ['date', 'updated_at']


# Nested serializers for detail views
class PatientDetailSerializer(PatientSerializer):
    appointments = AppointmentSerializer(many=True, read_only=True)
    medical_records = MedicalRecordSerializer(many=True, read_only=True)
    medical_reports = MedicalReportSerializer(many=True, read_only=True)
    bills = BillingSerializer(many=True, read_only=True)

    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + [
            'appointments',
            'medical_records',
            'medical_reports',
            'bills',
        ]

class AppointmentDetailSerializer(AppointmentSerializer):
    patient = PatientSerializer(read_only=True)
    medical_record = MedicalRecordSerializer(read_only=True)
