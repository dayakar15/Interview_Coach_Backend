import random
from django.db.models import Avg, Count

from evaluation.models import Evaluation
from interviews.models import Question
from .models import WeakArea, StudyPlan, StudyPlanItem
from .recommendations import get_recommendations

WEAK_THRESHOLD = 65.0  # overall_score below this is considered a weak area
MIN_ATTEMPTS_FOR_WEAKNESS = 1  # how many answered questions in a category before we judge it
PRACTICE_QUESTIONS_PER_TOPIC = 3


def compute_category_performance(user):
    """
    Aggregates Evaluation.overall_score by question category for a user,
    across all of their sessions (completed or not -- an answer that's
    already been scored is real signal even mid-session).
    """
    rows = (
        Evaluation.objects
        .filter(session_question__session__user=user)
        .values("session_question__question__category")
        .annotate(avg_score=Avg("overall_score"), attempts=Count("id"))
    )
    return {
        row["session_question__question__category"]: {
            "avg_score": round(row["avg_score"], 2),
            "attempts": row["attempts"],
        }
        for row in rows
    }


def refresh_weak_areas(user):
    """
    Recomputes WeakArea rows for a user from scratch based on current
    evaluation history. Returns the queryset of current WeakArea objects.
    """
    performance = compute_category_performance(user)

    seen_categories = set()
    for category, stats in performance.items():
        is_weak = (
            stats["attempts"] >= MIN_ATTEMPTS_FOR_WEAKNESS
            and stats["avg_score"] < WEAK_THRESHOLD
        )
        WeakArea.objects.update_or_create(
            user=user, category=category,
            defaults={
                "average_score": stats["avg_score"],
                "attempts": stats["attempts"],
                "is_weak": is_weak,
            },
        )
        seen_categories.add(category)

    # Drop stale rows for categories with no evaluations at all anymore.
    WeakArea.objects.filter(user=user).exclude(category__in=seen_categories).delete()

    return WeakArea.objects.filter(user=user).order_by("average_score")


def generate_study_plan(user):
    """
    Builds (or refreshes) the user's single live StudyPlan from their
    current WeakArea rows. If nothing qualifies as "weak", we still produce
    a light plan around the user's lowest-scoring category so the feature
    always returns something actionable rather than an empty state.
    """
    weak_areas = list(WeakArea.objects.filter(user=user).order_by("average_score"))
    if not weak_areas:
        return None

    plan, _created = StudyPlan.objects.update_or_create(user=user, defaults={})
    plan.items.all().delete()

    target_areas = [w for w in weak_areas if w.is_weak]
    if not target_areas:
        # Nobody is "weak" -- give light polish suggestions on the single
        # lowest-scoring category so the plan is never empty when there's
        # at least some answer history.
        target_areas = weak_areas[:1]
        plan.summary = (
            "No significant weak areas detected -- nice work. Here's a light "
            "refresher on your relatively weaker area to keep it sharp."
        )
    else:
        plan.summary = (
            f"{len(target_areas)} weak area(s) detected. Focus study time in "
            "priority order below, starting with the lowest score."
        )
    plan.save()

    for priority, weak_area in enumerate(target_areas, start=1):
        rec = get_recommendations(weak_area.category)
        candidate_ids = list(
            Question.objects.filter(category=weak_area.category, is_active=True)
            .values_list("id", flat=True)
        )
        practice_ids = random.sample(
            candidate_ids, k=min(PRACTICE_QUESTIONS_PER_TOPIC, len(candidate_ids))
        ) if candidate_ids else []

        StudyPlanItem.objects.create(
            plan=plan,
            category=weak_area.category,
            priority=priority,
            average_score=weak_area.average_score,
            recommended_topics=rec["topics"],
            recommended_resources=rec["resources"],
            practice_question_ids=practice_ids,
        )

    return plan


def refresh_weak_areas_and_plan(user):
    """Convenience entry point: recompute weak areas, then regenerate the plan."""
    refresh_weak_areas(user)
    return generate_study_plan(user)
