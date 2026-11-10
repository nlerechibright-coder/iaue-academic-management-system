from django.db import models
from django.conf import settings

class ApprovalAction(models.Model):
    """Logs every state change in the result workflow."""
    result_sheet = models.ForeignKey('results.ResultSheet', on_delete=models.CASCADE, related_name='approval_history')
    
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='performed_approvals')
    role_performed = models.CharField(max_length=20, help_text="HOD, DEAN, ER, LECTURER")
    
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('SUBMIT', 'Submitted'),
            ('APPROVE', 'Approved'),
            ('RETURN', 'Returned for Correction'),
            ('VERIFY', 'Verified Final'),
            ('PUBLISH', 'Published'),
        ]
    )
    
    comments = models.TextField(blank=True, help_text="Reason for return or general note")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.actor.username} performed {self.action_type} on {self.result_sheet.offering.course.code}"
