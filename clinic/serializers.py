"""
Serializers for the clinic API.
"""

from decimal import Decimal

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Patient, Appointment, MedicalRecord, MedicalReport,
    Prescription, Billing, BillingItem, ClinicStats
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
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_name', 'medication_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    


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

class BillingItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = BillingItem
            fields = ['id', 'medicine_name', 'amount']
            read_only_fields = ['id']

class BillingSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        source='patient',
        queryset=Patient.objects.all(),
        write_only=True,
        required=False
    )
    patient_name = serializers.SerializerMethodField()
    items = BillingItemSerializer(many=True, required=False)
    
    class Meta:
        model = Billing
        fields = [
            'id', 'patient', 'patient_id', 'patient_name',
            'amount', 'status', 'description', 'items', 'invoice_date',
            'due_date', 'payment_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'invoice_date']
        extra_kwargs = {
            'amount': {'required': False},
            'description': {'required': False, 'allow_blank': True},
        }
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        items = attrs.get('items')

        if items is not None:
            valid_items = [
                item for item in items
                if item.get('medicine_name') and item.get('amount') is not None
            ]
            if not valid_items:
                raise serializers.ValidationError({
                    'items': 'Add at least one medicine with a price.'
                })

        elif self.instance is None:
            if attrs.get('amount') is None or not attrs.get('description'):
                raise serializers.ValidationError(
                    'Provide either invoice items or both amount and description.'
                )

        return attrs

    def _build_description_from_items(self, items):
        medicine_names = [item['medicine_name'].strip() for item in items if item.get('medicine_name')]
        return ', '.join(medicine_names)

    def _sum_item_amounts(self, items):
        return sum(Decimal(str(item['amount'])) for item in items)

    def create(self, validated_data):
        items_data = validated_data.pop('items', None)

        if items_data:
            validated_data['amount'] = self._sum_item_amounts(items_data)
            validated_data['description'] = self._build_description_from_items(items_data)

        billing = Billing.objects.create(**validated_data)

        if items_data:
            BillingItem.objects.bulk_create(
                [
                    BillingItem(
                        billing=billing,
                        medicine_name=item['medicine_name'].strip(),
                        amount=item['amount'],
                    )
                    for item in items_data
                ]
            )

        return billing

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if items_data is not None:
            instance.items.all().delete()
            BillingItem.objects.bulk_create(
                [
                    BillingItem(
                        billing=instance,
                        medicine_name=item['medicine_name'].strip(),
                        amount=item['amount'],
                    )
                    for item in items_data
                    if item.get('medicine_name')
                ]
            )
            instance.amount = self._sum_item_amounts(items_data)
            instance.description = self._build_description_from_items(items_data)

        instance.save()
        return instance


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
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + [
            'appointments',
            'medical_records',
            'medical_reports',
            'bills',
            'prescriptions',
        ]

class AppointmentDetailSerializer(AppointmentSerializer):
    patient = PatientSerializer(read_only=True)
    medical_record = MedicalRecordSerializer(read_only=True)
