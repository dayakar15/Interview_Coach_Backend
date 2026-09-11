from django.test import TestCase
from interviews.models import Question
from .engines import RuleBasedEvaluator


def make_question(**overrides):
    defaults = dict(
        text="Explain binary search.",
        category="dsa",
        difficulty="easy",
        expected_keywords=["logarithmic", "sorted", "divide"],
        min_words=20,
    )
    defaults.update(overrides)
    return Question(**defaults)


class RuleBasedEvaluatorTests(TestCase):
    def setUp(self):
        self.evaluator = RuleBasedEvaluator()

    def test_empty_answer_scores_zero(self):
        q = make_question()
        result = self.evaluator.evaluate(q, "")
        self.assertEqual(result["overall_score"], 0)
        self.assertEqual(result["completeness_score"], 0)
        self.assertEqual(result["clarity_score"], 0)
        self.assertIn("No answer", result["feedback"])

    def test_strong_answer_scores_highly(self):
        q = make_question()
        answer = (
            "Binary search works on a sorted array by repeatedly dividing the search "
            "space in half. Because we divide the problem size by two at each step, "
            "the algorithm runs in logarithmic time, specifically O(log n). This makes "
            "it much faster than a linear scan for large sorted datasets."
        )
        result = self.evaluator.evaluate(q, answer)
        self.assertGreaterEqual(result["overall_score"], 85)
        self.assertEqual(set(result["matched_keywords"]), {"logarithmic", "sorted", "divide"})
        self.assertEqual(result["missed_keywords"], [])

    def test_short_answer_flagged_as_incomplete(self):
        q = make_question(min_words=30)
        result = self.evaluator.evaluate(q, "It uses divide and sorted logic.")
        self.assertLess(result["completeness_score"], 50)
        self.assertIn("short", result["feedback"].lower())

    def test_missing_keywords_are_listed(self):
        q = make_question(expected_keywords=["logarithmic", "sorted", "divide", "pivot"])
        answer = "Binary search is sorted and uses divide and conquer, running fast."
        result = self.evaluator.evaluate(q, answer)
        self.assertIn("pivot", result["missed_keywords"])
        self.assertIn("logarithmic", result["missed_keywords"])
        self.assertIn("pivot", result["feedback"])

    def test_filler_words_reduce_clarity_score(self):
        q = make_question(expected_keywords=[])
        clean = ("This approach divides the sorted array in half each time, so it runs "
                  "in logarithmic time and scales well for large inputs overall.")
        filler = ("So, um, it's like, you know, basically dividing the sorted array in "
                   "half each time, um, so it's like logarithmic, you know, kind of.")
        clean_result = self.evaluator.evaluate(q, clean)
        filler_result = self.evaluator.evaluate(q, filler)
        self.assertGreater(clean_result["clarity_score"], filler_result["clarity_score"])

    def test_no_expected_keywords_does_not_penalize(self):
        q = make_question(expected_keywords=[], min_words=5)
        result = self.evaluator.evaluate(q, "A short but complete answer here now.")
        self.assertEqual(result["keyword_coverage_score"], 100.0)

    def test_overall_score_is_weighted_composite(self):
        q = make_question(expected_keywords=["logarithmic"], min_words=10)
        result = self.evaluator.evaluate(q, "This is logarithmic and fairly clear overall today.")
        expected = round(
            0.5 * result["keyword_coverage_score"]
            + 0.3 * result["completeness_score"]
            + 0.2 * result["clarity_score"],
            2,
        )
        self.assertEqual(result["overall_score"], expected)
