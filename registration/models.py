# registration/models.py
from django.db import models
from students.models import StudentProfile
from academics.models import AcademicSession
from courses.models import CourseOffering

class CourseRegistration(models.Model):
    """
    Represents a student's enrollment bundle for a specific session/semester.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='registrations')
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='registrations')
    
    # Using CharField to match CourseOffering.semester_type logic directly
    semester_type = models.CharField(
        max_length=20,
        choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')],
        default='FIRST'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING', 'Pending Approval'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('WITHDRAWN', 'Withdrawn'),
        ],
        default='DRAFT'
    )
    
    total_credit_units = models.IntegerField(default=0)
    max_allowed_units = models.IntegerField(default=24)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'session', 'semester_type')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.matric_number} - {self.session.name} ({self.get_semester_type_display()})"

    def save(self, *args, **kwargs):
        # CRITICAL FIX: Only recalculate credits if the object already exists in DB (has a PK)
        # Prevents ValueError when accessing reverse relations on unsaved instances
        if self.pk:
            self.total_credit_units = sum(
                item.offering.course.credit_units 
                for item in self.registered_items.filter(status='ACTIVE')
            )
        
        super().save(*args, **kwargs)


class RegisteredCourseItem(models.Model):
    """
    Junction table linking Registration Header to specific Course Offerings.
    """
    registration = models.ForeignKey(CourseRegistration, on_delete=models.CASCADE, related_name='registered_items')
    offering = models.ForeignKey(CourseOffering, on_delete=models.PROTECT, related_name='registration_items')
    
    added_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='ACTIVE') 

    class Meta:
        unique_together = ('registration', 'offering')
        verbose_name_plural = "Registered Course Items"

    def __str__(self):
        return f"{self.registration.student.matric_number}: {self.offering.course.code}"
    
    def save(self, *args, **kwargs):
        # Always trigger parent recalculation when an item is saved
        super().save(*args, **kwargs)
        if self.registration_id:
            self.registration.save(update_fields=['total_credit_units'])