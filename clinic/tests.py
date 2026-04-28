"""
Tests for clinic API.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import Patient, Appointment, MedicalRecord


class PatientAPITestCase(TestCase):
    """Test Patient API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.patient_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'address': '123 Main St',
            'medical_history': 'Asthma'
        }
    
    def test_create_patient(self):
        """Test creating a new patient."""
        response = self.client.post('/api/patients/', self.patient_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'John')
    
    def test_list_patients(self):
        """Test listing patients."""
        Patient.objects.create(**self.patient_data)
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_get_patient_detail(self):
        """Test getting patient details."""
        patient = Patient.objects.create(**self.patient_data)
        response = self.client.get(f'/api/patients/{patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')


class AppointmentAPITestCase(TestCase):
    """Test Appointment API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.patient = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            date_of_birth='1990-01-01',
            gender='M',
            address='123 Main St'
        )
        
        self.appointment_data = {
            'patient': self.patient.id,
            'doctor_name': 'Dr. Smith',
            'appointment_date': (
                date.today() + timedelta(days=1)
            ).isoformat() + 'T10:00:00Z',
            'reason': 'Checkup',
            'status': 'scheduled'
        }
    
    def test_create_appointment(self):
        """Test creating an appointment."""
        response = self.client.post('/api/appointments/', self.appointment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_get_today_appointments(self):
        """Test getting today's appointments."""
        Appointment.objects.create(
            patient=self.patient,
            doctor_name='Dr. Smith',
            appointment_date=date.today(),
            reason='Checkup'
        )
        response = self.client.get('/api/appointments/today/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
