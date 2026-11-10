from django.db import models

class Course(models.Model):
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    department = models.ForeignKey('institution.Department', on_delete=models.CASCADE, related_name='courses')
    programme = models.ForeignKey('institution.Programme', on_delete=models.CASCADE, related_name='courses', null=True, blank=True, help_text="Leave blank if applicable to all programmes in the department.")
    level = models.IntegerField(help_text="e.g., 100, 200, 300")
    semester = models.CharField(max_length=10, choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')])
    credit_units = models.IntegerField()
    is_compulsory = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)

    class Meta:
        unique_together = ('code', 'department', 'level')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"

class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    session = models.ForeignKey('academics.AcademicSession', on_delete=models.CASCADE, related_name='offerings')
    semester_type = models.CharField(max_length=10, choices=[('FIRST', 'First Semester'), ('SECOND', 'Second Semester')])
    level = models.IntegerField()

    class Meta:
        unique_together = ('course', 'session', 'semester_type', 'level')
        ordering = ['session__name', 'course__code']

    def __str__(self):
        return f"{self.course.code} ({self.session.name} - {self.semester_type})"

class Section(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=10, help_text="e.g., A, B, Default")
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('offering', 'name')

    def __str__(self):
        return f"{self.offering.course.code} - Section {self.name}"

class LecturerAssignment(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='assignments')
    lecturer = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='assignments')

    class Meta:
        unique_together = ('offering', 'section', 'lecturer')

    def __str__(self):
        return f"{self.lecturer.user.get_full_name()} -> {self.section}"
