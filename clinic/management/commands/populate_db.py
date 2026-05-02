"""
Management command to populate database with sample data.
Creates doctors and their associated patients, appointments, and medical records.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clinic.models import (
    Patient, Appointment, MedicalRecord, MedicalReport,
    Prescription, Billing, ClinicStats
)
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample doctor, patient, and appointment data'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting database population...'))
        
        # Create superuser/admin for admin panel access
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@clinic.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                specialization='System Administrator'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created superuser: admin/admin123'))
        else:
            self.stdout.write('Admin user already exists')
        
        # Create sample doctors
        doctors = []
        doctor_data = [
            ('dr_smith', 'John', 'Smith', 'john@clinic.com', '555-0001', 'Cardiology'),
            ('dr_johnson', 'Sarah', 'Johnson', 'sarah@clinic.com', '555-0002', 'Neurology'),
            ('dr_williams', 'Michael', 'Williams', 'michael@clinic.com', '555-0003', 'Orthopedics'),
        ]
        
        for username, first_name, last_name, email, phone, specialization in doctor_data:
            doctor, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'specialization': specialization,
                    'is_active': True
                }
            )
            if created:
                doctor.set_password('doctor123')  # Default password for demo
                doctor.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created doctor: {username} ({specialization})'))
                doctors.append(doctor)
            else:
                self.stdout.write(f'Doctor {username} already exists')
                doctors.append(doctor)
        
        # Create sample patients for each doctor
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'Robert', 'Lisa']
        last_names = ['Doe', 'Smith', 'Johnson', 'Brown', 'Davis', 'Garcia', 'Martinez', 'Wilson']
        father_names = ['David', 'Tim','mathew']
        genders = ['M', 'F']
        
        patients = []
        patient_count = 0
        
        for doctor in doctors:
            # Create 4-6 patients per doctor
            num_patients = random.randint(4, 6)
            for _ in range(num_patients):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                email = f'{first_name.lower()}.{last_name.lower()}_{patient_count}@example.com'
                father_name = random.choice(father_names)
                patient, created = Patient.objects.get_or_create(
                    email=email,
                    defaults={
                        'doctor': doctor,
                        'first_name': first_name,
                        'last_name': last_name,
                        'father_name': father_name,
                        'phone': f'555-{random.randint(1000, 9999)}',
                        'date_of_birth': f'{random.randint(1950, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                        'gender': random.choice(genders),
                        'address': f'{random.randint(100, 999)} Main St, City, State',
                        'medical_history': random.choice([
                            'Hypertension, Diabetes',
                            'Asthma, Allergies',
                            'No significant history',
                            'Previous back injury',
                            'Migraine headaches'
                        ])
                    }
                )
                if created:
                    patients.append(patient)
                    patient_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {patient_count} patients across {len(doctors)} doctors'))
        
        # Create sample appointments
        appointment_count = 0
        for patient in patients[:len(patients)//2]:  # Appointments for half the patients
            num_appointments = random.randint(1, 3)
            for _ in range(num_appointments):
                appointment, created = Appointment.objects.get_or_create(
                    patient=patient,
                    appointment_date=datetime.now() + timedelta(days=random.randint(1, 60)),
                    defaults={
                        'doctor': patient.doctor,
                        'reason': random.choice([
                            'Regular checkup',
                            'Follow-up consultation',
                            'Chronic condition management',
                            'New complaint evaluation',
                            'Lab result review'
                        ]),
                        'status': random.choice(['scheduled', 'completed', 'cancelled']),
                        'notes': 'Patient appeared well'
                    }
                )
                if created:
                    appointment_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {appointment_count} appointments'))
        
        # Create sample medical records for completed appointments
        medical_record_count = 0
        completed_appointments = Appointment.objects.filter(status='completed')[:len(patients)//3]
        
        for appointment in completed_appointments:
            record, created = MedicalRecord.objects.get_or_create(
                appointment=appointment,
                defaults={
                    'patient': appointment.patient,
                    'doctor': appointment.doctor,
                    'diagnosis': random.choice([
                        'Hypertension (Stage 1)',
                        'Type 2 Diabetes Mellitus',
                        'Acute Upper Respiratory Infection',
                        'Migraine without aura',
                        'Generalized Anxiety Disorder'
                    ]),
                    'treatment': random.choice([
                        'Medication and lifestyle modifications',
                        'Antihypertensive therapy',
                        'Diabetes management with metformin',
                        'Rest and supportive care',
                        'Counseling and pharmacotherapy'
                    ]),
                    'medications': random.choice([
                        'Amlodipine 5mg daily',
                        'Metformin 500mg twice daily',
                        'Ibuprofen 400mg as needed',
                        'Sertraline 50mg daily',
                        'Atorvastatin 20mg nightly'
                    ]),
                    'vital_signs': {
                        'bp': f'{random.randint(110, 140)}/{random.randint(70, 90)}',
                        'temp': f'{random.uniform(98.0, 99.5):.1f}F',
                        'pulse': random.randint(60, 100),
                        'resp_rate': random.randint(14, 18),
                        'weight_kg': random.uniform(60, 100)
                    },
                    'follow_up_date': datetime.now().date() + timedelta(days=random.randint(7, 30))
                }
            )
            if created:
                medical_record_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {medical_record_count} medical records'))
        
        # Create sample prescriptions for medical records
        prescription_count = 0
        for record in MedicalRecord.objects.all()[:10]:
            num_prescriptions = random.randint(1, 3)
            for _ in range(num_prescriptions):
                prescription, created = Prescription.objects.get_or_create(
                    medical_record=record,
                    medication_name=random.choice([
                        'Lisinopril', 'Metformin', 'Atorvastatin', 'Omeprazole',
                        'Sertraline', 'Amlodipine', 'Aspirin', 'Ibuprofen'
                    ]),
                    defaults={
                        'dosage': random.choice(['500mg', '10mg', '20mg', '500mg', '100mg']),
                        'frequency': random.choice(['Once daily', 'Twice daily', 'Three times daily', 'As needed']),
                        'duration': random.choice(['7 days', '14 days', '30 days', '90 days']),
                        'instructions': 'Take with food, do not skip doses'
                    }
                )
                if created:
                    prescription_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {prescription_count} prescriptions'))
        
        # Create sample billing records
        billing_count = 0
        for patient in patients[:len(patients)//2]:
            num_bills = random.randint(1, 3)
            for _ in range(num_bills):
                billing, created = Billing.objects.get_or_create(
                    patient=patient,
                    invoice_date=datetime.now().date() - timedelta(days=random.randint(1, 60)),
                    defaults={
                        'amount': round(random.uniform(50, 500), 2),
                        'status': random.choice(['pending', 'paid', 'overdue']),
                        'description': random.choice(['Consultation fee', 'Lab tests', 'Procedure', 'Follow-up visit']),
                        'due_date': datetime.now().date() + timedelta(days=random.randint(7, 30)),
                        'payment_date': datetime.now().date() if random.choice([True, False, False]) else None
                    }
                )
                if created:
                    billing_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {billing_count} billing records'))
        
        # Create clinic statistics
        total_patients = Patient.objects.count()
        total_appointments = Appointment.objects.count()
        completed_appointments = Appointment.objects.filter(status='completed').count()
        total_revenue = sum(b.amount for b in Billing.objects.filter(status='paid'))
        pending_bills = sum(b.amount for b in Billing.objects.filter(status__in=['pending', 'overdue']))
        
        stats, created = ClinicStats.objects.get_or_create(
            date=datetime.now().date(),
            defaults={
                'total_patients': total_patients,
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'pending_bills': pending_bills,
                'total_revenue': total_revenue
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created clinic statistics'))
        else:
            self.stdout.write('Clinic statistics already exist for today')
        
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*60 +
            '\nDatabase population completed successfully!' +
            '\n' + '='*60 +
            '\nLogin credentials:' +
            '\nAdmins: /admin' +
            '\n  Username: admin' +
            '\n  Password: admin123' +
            '\nDoctors: API /api/token/' +
            '\n  Username: dr_smith (or dr_johnson, dr_williams)' +
            '\n  Password: doctor123' +
            '\n' + '='*60
        ))
