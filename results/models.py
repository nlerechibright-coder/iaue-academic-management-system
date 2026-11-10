from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ResultSheet(models.Model):
    """One sheet per Course Offering per Session/Semester."""
    offering = models.OneToOneField('courses.CourseOffering', on_delete=models.CASCADE, related_name='result_sheet')
    lecturer = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='submitted_sheets')
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft Entry'),
            ('SUBMITTED', 'Submitted to HOD'),
            ('RETURNED', 'Returned for Correction'),
            ('APPROVED_HOD', 'Approved by HOD'),
            ('APPROVED_DEAN', 'Approved by Dean'),
            ('VERIFIED_ER', 'Verified by Exams Records'),
            ('PUBLISHED', 'Published to Students'),
        ],
        default='DRAFT'
    )
    
    submission_date = models.DateTimeField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    # Metadata for CSV uploads
    upload_source = models.CharField(max_length=50, blank=True, help_text="Manual Entry or CSV Filename")
    
    class Meta:
        ordering = ['-submission_date']

    def __str__(self):
        return f"Results for {self.offering.course.code} ({self.offering.session.name})"

class StudentGrade(models.Model):
    """Individual student score within a Result Sheet."""
    result_sheet = models.ForeignKey(ResultSheet, on_delete=models.CASCADE, related_name='grades')
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='grades_received')
    
    # Assessment Breakdown
    ca_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(30)], default=0)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(70)], default=0)
    
    # Calculated Fields
    total_score = models.DecimalField(max_digits=5, decimal_places=2, editable=False)
    grade_letter = models.CharField(max_length=2, editable=False, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=1, editable=False, default=0)
    
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('result_sheet', 'student')
        ordering = ['student__matric_number']

    def save(self, *args, **kwargs):
        # Auto-calculate Total
        self.total_score = self.ca_score + self.exam_score
        
        # Auto-grading Logic (Standard Nigerian University Scale)
        score = float(self.total_score)
        if score >= 70:
            self.grade_letter = 'A'
            self.grade_point = 5.0
        elif score >= 60:
            self.grade_letter = 'B'
            self.grade_point = 4.0
        elif score >= 50:
            self.grade_letter = 'C'
            self.grade_point = 3.0
        elif score >= 45:
            self.grade_letter = 'D'
            self.grade_point = 2.0
        elif score >= 40:
            self.grade_letter = 'E'
            self.grade_point = 1.0
        else:
            self.grade_letter = 'F'
            self.grade_point = 0.0
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.matric_number}: {self.grade_letter} ({self.total_score})"
