# courses/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Course(models.Model):
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE, related_name='courses')
    programme = models.ForeignKey('institution.Programme', on_delete=models.CASCADE, related_name='courses', null=True, blank=True, help_text="Leave blank if applicable to all programmes in the department.")
    level = models.IntegerField(help_text="e.g., 100, 200, 300")
    semester = models.CharField(max_length=10, choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')])
    
    credit_units = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)], 
        default=3
    )
    
    is_compulsory = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_courses')

    class Meta:
        unique_together = ('code', 'department', 'level', 'semester')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"

    def clean(self):
        if self.pk and self.prerequisites.filter(pk=self.pk).exists():
            raise ValidationError("A course cannot be its own prerequisite.")


class CourseOffering(models.Model):
    """Represents a course being taught in a specific session/semester."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    session = models.ForeignKey('academics.AcademicSession', on_delete=models.CASCADE, related_name='offerings')
    semester_type = models.CharField(max_length=10, choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')])
    level = models.IntegerField()
    
    class Meta:
        unique_together = ('course', 'session', 'semester_type', 'level')
        ordering = ['session__name', 'course__code']
        verbose_name_plural = "Course Offerings"

    def __str__(self):
        return f"{self.course.code} ({self.session.name} - {self.get_semester_type_display()})"

    def get_registered_students_count(self):
        # Uses the related name from registration.models.CourseRegistration
        # Assuming related_name is 'registered_offerings' or similar in registration app
        try:
            return self.registrations.count()
        except AttributeError:
            return 0
            
    def is_available_for_student(self, student_profile):
        """Check eligibility logic."""
        if student_profile.department_id is None or self.course.department_id != student_profile.department_id:
            return False, "Department mismatch."

        if self.course.programme_id and student_profile.programme_id and self.course.programme_id != student_profile.programme_id:
            return False, "Programme restriction applies."

        if self.course.programme_id and not student_profile.programme_id:
            return False, "Student programme is not assigned."

        student_level = getattr(student_profile, 'current_level', getattr(student_profile, 'level', 0))
        offering_level = self.level

        if offering_level == student_level:
            return True, "Current level course."
        if offering_level < student_level:
            return True, "Eligible for carryover registration."
        return False, "Level too high for current status."


class LecturerAssignment(models.Model):
    """Assigns a lecturer to a Course Offering directly (No Sections)."""
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='assignments')
    lecturer = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('offering', 'lecturer')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.lecturer.user.get_full_name()} -> {self.offering.course.code}"