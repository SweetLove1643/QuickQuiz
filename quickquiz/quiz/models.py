from django.db import models
from core.models import Document

class Question(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    options_answer = models.JSONField(null=True, blank=True)  # lưu trữ các lựa chọn A/B/C/D nếu có
    correct_answer = models.TextField()  # đáp án đúng
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q for {self.document_id}: {self.question_text[:50]}"

class UserAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    user_response = models.TextField()
    score = models.FloatField(null=True, blank=True)        # ví dụ 0-1 hoặc 0-100
    created_at = models.DateTimeField(auto_now_add=True)
