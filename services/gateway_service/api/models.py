import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    extracted_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"{self.file_name} (User: {self.user.username})"
        return f"{self.file_name} (User: None)"
