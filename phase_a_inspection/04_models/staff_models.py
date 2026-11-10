from django.db import models
from django.conf import settings
from django.utils import timezone

class StaffProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    staff_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"

class Appointment(models.Model):
    ROLE_CHOICES = [
        ('LECTURER', 'Lecturer'),
        ('HOD', 'Head of Department'),
        ('DEAN', 'Dean'),
        ('VC', 'Vice Chancellor'),
        ('EXAMS_RECORDS', 'Exams and Records'),
    ]

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='appointments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    faculty = models.ForeignKey('institution.Faculty', on_delete=models.CASCADE, null=True, blank=True, help_text="Required for Dean")
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE, null=True, blank=True, help_text="Required for HOD")
    
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    appointed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='made_appointments')
    revocation_reason = models.TextField(blank=True, null=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_appointments')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_role_display()}"

    @property
    def is_currently_valid(self):
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
