from django.db import models

class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g., 2023/2024")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicSession.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class Semester(models.Model):
    SEMESTER_CHOICES = [
        ('FIRST', 'First Semester'),
        ('SECOND', 'Second Semester'),
    ]
    name = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='semesters')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session', 'name')
        ordering = ['-session__name', 'name']

    def __str__(self):
        return f"{self.get_name_display()} - {self.session.name}"

    def save(self, *args, **kwargs):
        if self.is_active:
            Semester.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
