from django.contrib import admin
from .models import Evaluation

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("id", "session_question", "overall_score", "engine", "created_at")
