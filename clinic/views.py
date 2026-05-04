"""
API Views for the clinic management system.

Only doctors can access the API for managing their own patients.
Admins access the Django admin dashboard (not this API).
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Sum
from datetime import timedelta

from .models import (
    Patient, Appointment, MedicalRecord, MedicalReport,
    Prescription, Billing, ClinicStats
)
from .serializers import (
    UserSerializer,
    PatientSerializer, PatientDetailSerializer,
    AppointmentSerializer, AppointmentDetailSerializer,
    MedicalRecordSerializer, MedicalReportSerializer,
    BillingSerializer, ClinicStatsSerializer,
    PrescriptionSerializer
)
from .permissions import IsDoctorUser, IsOwnDoctor, IsOwnDoctorQueryset

User = get_user_model()


class UserRegisterViewSet(viewsets.ViewSet):
    """
    ViewSet for Doctor registration and authentication.
    
    Register: POST /api/auth/register/
    Profile: GET /api/auth/profile/
    Profile Update: PATCH /api/auth/profile/
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a new doctor account.
        Required fields: username, email, password, first_name, last_name, specialization
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsDoctorUser])
    def profile(self, request):
        """Get current doctor's profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsDoctorUser])
    def update_profile(self, request):
        """Update current doctor's profile."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient management.
    
    Doctors can only view/manage their own patients.
    - List: GET /api/patients/ (only doctor's patients)
    - Create: POST /api/patients/
    - Detail: GET /api/patients/{id}/
    - Update: PATCH /api/patients/{id}/
    - Delete: DELETE /api/patients/{id}/
    """
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser, IsOwnDoctorQueryset]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['created_at', 'first_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter patients by current doctor."""
        return Patient.objects.filter(doctor=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PatientDetailSerializer
        return PatientSerializer
    
    def perform_create(self, serializer):
        """Automatically set the doctor to current user."""
        serializer.save(doctor=self.request.user)
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Get complete medical history for a patient."""
        patient = self.get_object()
        # Check permission
        if patient.doctor != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        medical_records = patient.medical_records.all()
        serializer = MedicalRecordSerializer(medical_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def upcoming_appointments(self, request, pk=None):
        """Get upcoming appointments for a patient."""
        patient = self.get_object()
        if patient.doctor != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        appointments = patient.appointments.filter(
            appointment_date__gte=timezone.now(),
            status='scheduled'
        ).order_by('appointment_date')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def billing_summary(self, request, pk=None):
        """Get billing summary for a patient."""
        patient = self.get_object()
        if patient.doctor != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        bills = patient.bills.all()
        summary = {
            'total_bills': bills.count(),
            'paid_amount': bills.filter(status='paid').aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'pending_amount': bills.filter(status='pending').aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'overdue_amount': bills.filter(status='overdue').aggregate(
                Sum('amount'))['amount__sum'] or 0,
        }
        return Response(summary)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment management.
    
    Doctors only see/manage appointments for their own patients.
    - List: GET /api/appointments/ (only doctor's appointments)
    - Create: POST /api/appointments/
    - Detail: GET /api/appointments/{id}/
    - Update: PATCH /api/appointments/{id}/
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctorUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name']
    ordering_fields = ['appointment_date', 'created_at', 'status']
    ordering = ['-appointment_date']
    
    def get_queryset(self):
        """Filter appointments by current doctor."""
        return Appointment.objects.filter(doctor=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AppointmentDetailSerializer
        return AppointmentSerializer
    
    def perform_create(self, serializer):
        """Automatically set the doctor to current user."""
        serializer.save(doctor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get all appointments for today."""
        today = timezone.now().date()
        appointments = self.get_queryset().filter(
            appointment_date__date=today,
            status='scheduled'
        )
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments (next 7 days)."""
        now = timezone.now()
        week_later = now + timedelta(days=7)
        appointments = self.get_queryset().filter(
            appointment_date__gte=now,
            appointment_date__lte=week_later,
            status='scheduled'
        )
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark appointment as completed."""
        appointment = self.get_object()
        appointment.status = 'completed'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment."""
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Medical Records management.
    
    Doctors only manage records for their own patients.
    - List: GET /api/medical-records/
    - Create: POST /api/medical-records/
    - Detail: GET /api/medical-records/{id}/
    - Update: PATCH /api/medical-records/{id}/
    """
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsDoctorUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name', 'diagnosis']
    ordering_fields = ['created_at', 'follow_up_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter medical records by current doctor."""
        return MedicalRecord.objects.filter(doctor=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set the doctor to current user."""
        serializer.save(doctor=self.request.user)


class MedicalReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Medical Reports (File uploads).
    
    Doctors only manage reports for their own patients.
    - List: GET /api/medical-reports/
    - Create: POST /api/medical-reports/ (with file upload)
    - Detail: GET /api/medical-reports/{id}/
    - Delete: DELETE /api/medical-reports/{id}/
    """
    serializer_class = MedicalReportSerializer
    permission_classes = [IsDoctorUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name', 'report_type']
    ordering_fields = ['created_at', 'report_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter medical reports by current doctor's patients."""
        return MedicalReport.objects.filter(patient__doctor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get reports grouped by type."""
        report_type = request.query_params.get('type')
        if report_type:
            reports = self.get_queryset().filter(report_type=report_type)
            serializer = self.get_serializer(reports, many=True)
            return Response(serializer.data)
        return Response({'error': 'type parameter required'}, status=status.HTTP_400_BAD_REQUEST)


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Prescription management.
    
    Doctors only manage prescriptions for their own patients.
    - List: GET /api/prescriptions/
    - Create: POST /api/prescriptions/
    - Detail: GET /api/prescriptions/{id}/
    - Update: PATCH /api/prescriptions/{id}/
    - Bulk Create: POST /api/prescriptions/bulk_create/
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctorUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['medication_name', 'patient__first_name', 'patient__last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter prescriptions by current doctor's patients."""
        queryset = Prescription.objects.filter(patient__doctor=self.request.user)
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=parse_date(date_from))
        if date_to:
            queryset = queryset.filter(created_at__date__lte=parse_date(date_to))
        
        return queryset

    def perform_create(self, serializer):
        """Save prescription with patient relationship."""
        patient = serializer.validated_data['patient']
        if patient.doctor != self.request.user:
            raise ValidationError({'patient': 'Patient not found or not authorized'})
        serializer.save()

    def perform_update(self, serializer):
        """Ensure prescriptions stay scoped to the current doctor's patients."""
        patient = serializer.validated_data.get('patient', serializer.instance.patient)
        if patient.doctor != self.request.user:
            raise ValidationError({'patient': 'Patient not found or not authorized'})
        serializer.save()
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests for prescription updates."""
        prescription = self.get_object()
        serializer = self.get_serializer(prescription, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple prescriptions for a patient.
        
        Request body:
        {
            "patient": 1,
            "prescriptions": [
                {
                    "medication_name": "Aspirin",
                    "dosage": "500mg",
                    "frequency": "twice_daily",
                    "duration": "7 days",
                    "instructions": "Take with food"
                }
            ]
        }
        """
        patient_id = request.data.get('patient')
        prescriptions_data = request.data.get('prescriptions', [])
        
        if not patient_id:
            return Response(
                {'error': 'patient field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            patient = Patient.objects.get(id=patient_id, doctor=request.user)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found or not authorized'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_prescriptions = []
        for presc_data in prescriptions_data:
            presc = Prescription.objects.create(
                patient=patient,
                **presc_data
            )
            created_prescriptions.append(presc)
        
        serializer = PrescriptionSerializer(created_prescriptions, many=True)
        return Response(
            {'created': len(created_prescriptions), 'prescriptions': serializer.data},
            status=status.HTTP_201_CREATED
        )

class BillingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Billing/Invoice management.
    
    Doctors only view billing for their own patients.
    - List: GET /api/billing/
    - Create: POST /api/billing/
    - Detail: GET /api/billing/{id}/
    - Update: PATCH /api/billing/{id}/
    """
    serializer_class = BillingSerializer
    permission_classes = [IsDoctorUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name', 'status']
    ordering_fields = ['invoice_date', 'amount', 'status']
    ordering = ['-invoice_date']
    
    def get_queryset(self):
        """Filter billing by current doctor's patients."""
        return Billing.objects.filter(patient__doctor=self.request.user)

    def perform_create(self, serializer):
        """Ensure invoices can only be created for the current doctor's patients."""
        patient = serializer.validated_data['patient']
        if patient.doctor != self.request.user:
            raise ValidationError({'patient_id': 'Patient not found or not authorized'})
        serializer.save()

    def perform_update(self, serializer):
        """Ensure invoices remain scoped to the current doctor's patients."""
        patient = serializer.validated_data.get('patient', serializer.instance.patient)
        if patient.doctor != self.request.user:
            raise ValidationError({'patient_id': 'Patient not found or not authorized'})
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get billing summary statistics for doctor's patients."""
        queryset = self.get_queryset()
        summary = {
            'total_pending': queryset.filter(status='pending').aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'total_overdue': queryset.filter(status='overdue').aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'total_paid': queryset.filter(status='paid').aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'total_revenue': queryset.aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'pending_count': queryset.filter(status='pending').count(),
            'overdue_count': queryset.filter(status='overdue').count(),
        }
        return Response(summary)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark billing as paid."""
        billing = self.get_object()
        billing.status = 'paid'
        billing.payment_date = timezone.now().date()
        billing.save()
        serializer = self.get_serializer(billing)
        return Response(serializer.data)


class ClinicStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Clinic Statistics (read-only).
    Admins manage stats through Django admin.
    """
    queryset = ClinicStats.objects.all()
    serializer_class = ClinicStatsSerializer
    permission_classes = [IsDoctorUser]
    ordering = ['-date']


class DashboardSummaryViewSet(viewsets.ViewSet):
    """
    Compact doctor dashboard summary.

    Endpoint: GET /api/summary/
    """
    permission_classes = [IsDoctorUser]

    def list(self, request):
        now = timezone.now()
        today = now.date()
        week_later = now + timedelta(days=7)

        patients_qs = Patient.objects.filter(doctor=request.user)
        appointments_qs = Appointment.objects.filter(doctor=request.user)
        billing_qs = Billing.objects.filter(patient__doctor=request.user)
        medical_records_qs = MedicalRecord.objects.filter(doctor=request.user)

        payload = {
            'patients': {
                'total': patients_qs.count(),
                'new_last_30_days': patients_qs.filter(
                    created_at__gte=now - timedelta(days=30)
                ).count(),
            },
            'appointments': {
                'today_scheduled': appointments_qs.filter(
                    appointment_date__date=today,
                    status='scheduled'
                ).count(),
                'upcoming_next_7_days': appointments_qs.filter(
                    appointment_date__gte=now,
                    appointment_date__lte=week_later,
                    status='scheduled'
                ).count(),
                'completed_total': appointments_qs.filter(status='completed').count(),
                'cancelled_total': appointments_qs.filter(status='cancelled').count(),
            },
            'billing': {
                'pending_amount': billing_qs.filter(status='pending').aggregate(
                    Sum('amount')
                )['amount__sum'] or 0,
                'overdue_amount': billing_qs.filter(status='overdue').aggregate(
                    Sum('amount')
                )['amount__sum'] or 0,
                'paid_amount': billing_qs.filter(status='paid').aggregate(
                    Sum('amount')
                )['amount__sum'] or 0,
                'pending_count': billing_qs.filter(status='pending').count(),
            },
            'medical_records': {
                'total': medical_records_qs.count(),
                'created_last_30_days': medical_records_qs.filter(
                    created_at__gte=now - timedelta(days=30)
                ).count(),
            },
        }
        return Response(payload)
