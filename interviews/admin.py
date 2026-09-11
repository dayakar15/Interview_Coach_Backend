from django.contrib import admin
from .models import Question, InterviewSession, SessionQuestion, Answer

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "difficulty", "is_active", "text")
    list_filter = ("category", "difficulty", "is_active")
    search_fields = ("text",)

@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "status", "started_at", "completed_at")
    list_filter = ("status", "category")

admin.site.register(SessionQuestion)
admin.site.register(Answer)
