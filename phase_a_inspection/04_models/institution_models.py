from django.db import models

class Faculty(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('faculty', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.faculty.name}"

class Programme(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    max_level = models.IntegerField(help_text="Maximum academic level (e.g., 400, 500, 600)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('department', 'code')

    def __str__(self):
        return f"{self.name} ({self.code})"
