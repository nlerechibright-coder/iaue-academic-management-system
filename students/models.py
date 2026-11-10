# students/models.py
from django.db import models
from django.conf import settings
from institution.models import Department, Programme
import datetime

class StudentProfile(models.Model):
    QUALIFICATION_CHOICES = [
        ('UNDERGRADUATE', 'Undergraduate'),
        ('POSTGRADUATE', 'Postgraduate'),
    ]
    
    LEVEL_CHOICES = [
        (100, '100 Level'),
        (200, '200 Level'),
        (300, '300 Level'),
        (400, '400 Level'),
        (500, '500 Level'),
        (600, '600 Level'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    matric_number = models.CharField(max_length=50, unique=True, blank=True) # Blank allowed initially, filled on save
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    level = models.IntegerField(choices=LEVEL_CHOICES, default=100)
    qualification_type = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES, default='UNDERGRADUATE')
    date_of_birth = models.DateField(null=True, blank=True)
    admission_year = models.IntegerField(default=datetime.date.today().year)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def current_level(self):
        return self.level

    def __str__(self):
        return f"{self.matric_number} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        # Auto-generate matric number if not provided
        if not self.matric_number:
            self.matric_number = self.generate_matric_number()
        
        # Set admission year to current year if new record
        if not self.pk:
            self.admission_year = datetime.date.today().year
            
        super().save(*args, **kwargs)

    def generate_matric_number(self):
        """
        Generates matric number in format u/YYYY/NNNNN
        Sequence resets/increments per year.
        """
        current_year = datetime.date.today().year
        prefix = f"u/{current_year}/"
        
        # Find the highest existing matric number for this year
        last_student = StudentProfile.objects.filter(
            matric_number__startswith=prefix
        ).order_by('-matric_number').first()
        
        if last_student:
            try:
                # Extract the numeric part after the prefix
                seq_str = last_student.matric_number.split('/')[-1]
                next_seq = int(seq_str) + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
            
        # Format with leading zeros (e.g., 00001)
        formatted_seq = str(next_seq).zfill(5)
        return f"{prefix}{formatted_seq}"