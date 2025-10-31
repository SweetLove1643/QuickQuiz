from django.db import models

# Create your models here.
class Document(models.Model):
    uploaded_file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)     # text từ OCR
    summary_text = models.TextField(blank=True)       # tóm tắt
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename