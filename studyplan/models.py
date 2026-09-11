from django.conf import settings
from django.db import models
from interviews.models import Question


class WeakArea(models.Model):
    """
    One row per (user, category) summarizing performance in that category.
    Recomputed wholesale each time `refresh_weak_areas_and_plan` runs, so
    it always reflects the user's current standing rather than a snapshot.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weak_areas")
    category = models.CharField(max_length=20, choices=Question.CATEGORY_CHOICES)
    average_score = models.FloatField()
    attempts = models.PositiveIntegerField()
    is_weak = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "category")
        ordering = ["average_score"]

    def __str__(self):
        return f"{self.user.username}/{self.category}: {self.average_score} ({'weak' if self.is_weak else 'ok'})"


class StudyPlan(models.Model):
    """
    Latest generated plan for a user. We keep exactly one live plan per user
    (OneToOne) rather than a history table -- a coach app cares about "what
    should I study now", not an archive of past plans. If plan history
    becomes a requirement later, this is a straightforward model to version.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_plan")
    generated_at = models.DateTimeField(auto_now=True)
    summary = models.TextField(blank=True, default="")

    def __str__(self):
        return f"StudyPlan for {self.user.username}"


class StudyPlanItem(models.Model):
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="items")
    category = models.CharField(max_length=20, choices=Question.CATEGORY_CHOICES)
    priority = models.PositiveIntegerField(help_text="1 = highest priority")
    average_score = models.FloatField()
    recommended_topics = models.JSONField(default=list, blank=True)
    recommended_resources = models.JSONField(default=list, blank=True)
    practice_question_ids = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["priority"]

    def __str__(self):
        return f"{self.plan.user.username} -> {self.category} (priority {self.priority})"
