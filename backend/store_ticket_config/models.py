from django.db import models


# Create your models here.
severity_choices = (
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
)
STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
class ticketConfig(models.Model):
    dc_user= models.CharField(max_length=50)
    dc_id = models.BigIntegerField()
    reason= models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,default='open')
    severity = models.CharField(max_length=10,choices=severity_choices, default='low')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at=models.DateTimeField(auto_now_add=True)
    ticket_channel_id = models.BigIntegerField(unique=True) 
    resolved_at = models.DateTimeField(null=True, blank=True) 
    resolved_by_username = models.CharField(max_length=100, null=True, blank=True)
    resolved_by_id = models.CharField(null=True, blank=True)


    def __str__(self):
        return f"Ticket #{self.ticket_channel_id}"  
