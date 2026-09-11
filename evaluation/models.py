from django.db import models
from interviews.models import SessionQuestion


class Evaluation(models.Model):
    """
    One evaluation per answered question. Scores are stored as 0-100 so the
    scale is stable regardless of which evaluator engine produced them.
    """

    session_question = models.OneToOneField(
        SessionQuestion, on_delete=models.CASCADE, related_name="evaluation"
    )
    keyword_coverage_score = models.FloatField(help_text="0-100")
    completeness_score = models.FloatField(help_text="0-100, based on answer depth/length")
    clarity_score = models.FloatField(help_text="0-100, structure/filler-word heuristic")
    overall_score = models.FloatField(help_text="0-100 weighted composite")
    matched_keywords = models.JSONField(default=list, blank=True)
    missed_keywords = models.JSONField(default=list, blank=True)
    feedback = models.TextField(blank=True, default="")
    engine = models.CharField(max_length=30, default="rule_based")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def category(self):
        return self.session_question.question.category

    def __str__(self):
        return f"Eval SQ#{self.session_question_id} score={self.overall_score}"
