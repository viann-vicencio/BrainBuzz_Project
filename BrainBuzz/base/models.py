from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

class QuizHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    grade = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_taken = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quiz for {self.user.username} - {self.title or 'Untitled'} - {self.last_taken.strftime('%Y-%m-%d %H:%M')}"

class Question(models.Model):
    quiz_history = models.ForeignKey(QuizHistory, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.question_text

class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
