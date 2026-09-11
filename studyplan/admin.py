from django.contrib import admin
from .models import WeakArea, StudyPlan, StudyPlanItem

@admin.register(WeakArea)
class WeakAreaAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "average_score", "attempts", "is_weak")

class StudyPlanItemInline(admin.TabularInline):
    model = StudyPlanItem
    extra = 0

@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "generated_at")
    inlines = [StudyPlanItemInline]
