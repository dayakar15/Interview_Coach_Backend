from django.contrib.auth import get_user_model
from django.test import TestCase

from interviews.models import Question, InterviewSession, SessionQuestion, Answer
from evaluation.models import Evaluation
from .services import refresh_weak_areas_and_plan
from .models import WeakArea

User = get_user_model()


def make_evaluated_answer(user, category, score):
    """Helper: create a fully-wired Question -> Session -> Answer -> Evaluation
    chain with a specific overall_score, without going through the real
    evaluator (we're testing aggregation/plan logic here, not scoring)."""
    question = Question.objects.create(text=f"Q in {category}", category=category, min_words=5)
    session = InterviewSession.objects.create(user=user, category=category)
    sq = SessionQuestion.objects.create(session=session, question=question, order=1)
    Answer.objects.create(session_question=sq, text="some answer text")
    Evaluation.objects.create(
        session_question=sq,
        keyword_coverage_score=score, completeness_score=score, clarity_score=score,
        overall_score=score, matched_keywords=[], missed_keywords=[],
    )
    return sq


class WeakAreaDetectionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="grace", password="StrongPass123!")

    def test_low_scoring_category_flagged_weak(self):
        make_evaluated_answer(self.user, "dsa", 40)
        make_evaluated_answer(self.user, "dsa", 50)
        refresh_weak_areas_and_plan(self.user)
        weak = WeakArea.objects.get(user=self.user, category="dsa")
        self.assertTrue(weak.is_weak)
        self.assertEqual(weak.average_score, 45.0)
        self.assertEqual(weak.attempts, 2)

    def test_high_scoring_category_not_flagged_weak(self):
        make_evaluated_answer(self.user, "behavioral", 90)
        refresh_weak_areas_and_plan(self.user)
        weak = WeakArea.objects.get(user=self.user, category="behavioral")
        self.assertFalse(weak.is_weak)

    def test_weak_areas_recompute_on_refresh(self):
        make_evaluated_answer(self.user, "dsa", 30)
        refresh_weak_areas_and_plan(self.user)
        self.assertTrue(WeakArea.objects.get(user=self.user, category="dsa").is_weak)

        # Improve performance and refresh again -- should flip to not-weak.
        make_evaluated_answer(self.user, "dsa", 95)
        make_evaluated_answer(self.user, "dsa", 95)
        refresh_weak_areas_and_plan(self.user)
        weak = WeakArea.objects.get(user=self.user, category="dsa")
        self.assertFalse(weak.is_weak)
        self.assertEqual(weak.attempts, 3)


class StudyPlanGenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="heidi", password="StrongPass123!")

    def test_no_evaluations_yields_no_plan(self):
        plan = refresh_weak_areas_and_plan(self.user)
        self.assertIsNone(plan)

    def test_plan_prioritizes_weakest_category_first(self):
        make_evaluated_answer(self.user, "dsa", 20)
        make_evaluated_answer(self.user, "system_design", 40)
        make_evaluated_answer(self.user, "backend", 90)

        plan = refresh_weak_areas_and_plan(self.user)
        self.assertIsNotNone(plan)
        categories_in_order = [item.category for item in plan.items.all()]
        # Only weak categories (score < 65) should appear, weakest first.
        self.assertEqual(categories_in_order, ["dsa", "system_design"])
        self.assertNotIn("backend", categories_in_order)

    def test_plan_items_include_topics_and_resources(self):
        make_evaluated_answer(self.user, "dsa", 20)
        # give it a practice question to recommend
        Question.objects.create(text="extra dsa q", category="dsa", is_active=True)

        plan = refresh_weak_areas_and_plan(self.user)
        item = plan.items.first()
        self.assertTrue(len(item.recommended_topics) > 0)
        self.assertTrue(len(item.recommended_resources) > 0)
        self.assertTrue(len(item.practice_question_ids) > 0)

    def test_plan_falls_back_to_light_polish_when_nothing_weak(self):
        make_evaluated_answer(self.user, "dsa", 90)
        make_evaluated_answer(self.user, "behavioral", 80)
        plan = refresh_weak_areas_and_plan(self.user)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.items.count(), 1)
        self.assertIn("No significant weak areas", plan.summary)

    def test_regenerating_plan_replaces_old_items(self):
        make_evaluated_answer(self.user, "dsa", 20)
        plan1 = refresh_weak_areas_and_plan(self.user)
        first_item_count = plan1.items.count()

        make_evaluated_answer(self.user, "databases", 10)
        plan2 = refresh_weak_areas_and_plan(self.user)

        self.assertEqual(plan1.pk, plan2.pk)  # same live plan, not a duplicate row
        self.assertEqual(plan2.items.count(), first_item_count + 1)
