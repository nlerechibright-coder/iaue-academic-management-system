from django.db import models
from django.conf import settings

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    matric_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('institution.Department', on_delete=models.SET_NULL, null=True)
    programme = models.ForeignKey('institution.Programme', on_delete=models.SET_NULL, null=True)
    current_level = models.IntegerField(help_text="e.g., 100, 200, 300")
    admission_session = models.CharField(max_length=20, help_text="e.g., 2023/2024")
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['matric_number']

    def __str__(self):
        return f"{self.matric_number} - {self.user.get_full_name()}"

    @staticmethod
    def generate_matric_number(admission_year):
        """Generate matric number in format U/YYYY/NNNNN"""
        last_student = StudentProfile.objects.filter(
            admission_session__startswith=str(admission_year)
        ).order_by('-matric_number').first()
        
        if last_student:
            last_num = int(last_student.matric_number.split('/')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"U/{admission_year}/{next_num:05d}"
