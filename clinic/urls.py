"""
URL routing for the clinic app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserRegisterViewSet,
    PatientViewSet, AppointmentViewSet, MedicalRecordViewSet,
    MedicalReportViewSet, PrescriptionViewSet, BillingViewSet,
    ClinicStatsViewSet, DashboardSummaryViewSet
)

router = DefaultRouter()
router.register(r'auth', UserRegisterViewSet, basename='auth')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'medical-records', MedicalRecordViewSet, basename='medical-record')
router.register(r'medical-reports', MedicalReportViewSet, basename='medical-report')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'billing', BillingViewSet, basename='billing')
router.register(r'stats', ClinicStatsViewSet, basename='stats')
router.register(r'summary', DashboardSummaryViewSet, basename='summary')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
