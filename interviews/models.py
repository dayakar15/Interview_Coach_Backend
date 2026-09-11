from django.conf import settings
from django.db import models


class Question(models.Model):
    """
    A bank question. `expected_keywords` drives the rule-based evaluator's
    coverage score -- it's a cheap stand-in for "does the answer touch the
    concepts a good answer should touch". `ideal_answer` is optional
    reference text used for future similarity-based scoring.
    """

    CATEGORY_CHOICES = [
        ("dsa", "Data Structures & Algorithms"),
        ("system_design", "System Design"),
        ("databases", "Databases"),
        ("behavioral", "Behavioral"),
        ("backend", "Backend / APIs"),
        ("frontend", "Frontend"),
        ("devops", "DevOps"),
    ]
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    text = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    expected_keywords = models.JSONField(
        default=list, blank=True,
        help_text="List of concept keywords a strong answer should mention.",
    )
    ideal_answer = models.TextField(blank=True, default="")
    min_words = models.PositiveIntegerField(
        default=25, help_text="Below this word count, an answer is flagged as too thin."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}/{self.difficulty}] {self.text[:60]}"


class InterviewSession(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions"
    )
    category = models.CharField(
        max_length=20, choices=Question.CATEGORY_CHOICES, blank=True, default="",
        help_text="Empty means mixed-category session.",
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="in_progress")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session #{self.pk} ({self.user.username}, {self.status})"

    @property
    def average_score(self):
        from evaluation.models import Evaluation
        evals = Evaluation.objects.filter(session_question__session=self)
        if not evals.exists():
            return None
        return round(sum(e.overall_score for e in evals) / evals.count(), 2)


class SessionQuestion(models.Model):
    """
    Through-table linking a session to the ordered questions it asked.
    Keeping this separate from Question lets the same Question be reused
    across many sessions/users without duplication.
    """

    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="session_questions"
    )
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("session", "order")

    def __str__(self):
        return f"SQ#{self.pk} session={self.session_id} q={self.question_id}"


class Answer(models.Model):
    session_question = models.OneToOneField(
        SessionQuestion, on_delete=models.CASCADE, related_name="answer"
    )
    text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to SQ#{self.session_question_id}"
