from django.contrib import admin
from .models import QuizHistory, Question, Note

admin.site.register(QuizHistory)
admin.site.register(Question)
admin.site.register(Note)
