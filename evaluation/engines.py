"""
Evaluator engines.

Design: `BaseEvaluator.evaluate()` returns a plain dict with a fixed shape.
Callers (the `evaluate_answer` service function) never care which engine
produced it. This means:
  - Tests can run against RuleBasedEvaluator with zero network calls.
  - Swapping to a real LLM later is a one-line settings change, and the
    calling code (session views, weak-area detection, study plans) needs
    no changes because the output contract is identical.
"""

import re
from abc import ABC, abstractmethod

FILLER_WORDS = {"um", "uh", "like", "you know", "sort of", "kind of", "basically", "actually"}


class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(self, question, answer_text: str) -> dict:
        """
        Returns:
        {
            "keyword_coverage_score": float 0-100,
            "completeness_score": float 0-100,
            "clarity_score": float 0-100,
            "overall_score": float 0-100,
            "matched_keywords": [...],
            "missed_keywords": [...],
            "feedback": str,
        }
        """
        raise NotImplementedError


class RuleBasedEvaluator(BaseEvaluator):
    """
    Deterministic heuristic evaluator. Not as smart as an LLM grader, but:
      - free and instant
      - fully unit-testable (same input -> same output, always)
      - a reasonable default so the product works before any AI key is configured
    """

    KEYWORD_WEIGHT = 0.5
    COMPLETENESS_WEIGHT = 0.3
    CLARITY_WEIGHT = 0.2

    def evaluate(self, question, answer_text: str) -> dict:
        text = (answer_text or "").strip()
        words = re.findall(r"[a-zA-Z0-9']+", text)
        word_count = len(words)
        lower_text = text.lower()

        # --- Keyword coverage ---
        expected = [k.lower() for k in (question.expected_keywords or [])]
        matched = [k for k in expected if k in lower_text]
        missed = [k for k in expected if k not in lower_text]
        if expected:
            keyword_score = round(100 * len(matched) / len(expected), 2)
        else:
            keyword_score = 100.0  # nothing to check against; don't penalize

        # --- Completeness (depth proxy via word count vs min_words) ---
        if word_count == 0:
            completeness_score = 0.0
        else:
            completeness_score = round(min(100.0, 100 * word_count / max(question.min_words, 1)), 2)

        # --- Clarity (structure + filler-word heuristic) ---
        if word_count == 0:
            clarity_score = 0.0
        else:
            sentence_count = max(1, len(re.findall(r"[.!?]+", text)))
            avg_sentence_len = word_count / sentence_count
            filler_hits = sum(lower_text.count(f) for f in FILLER_WORDS)
            filler_penalty = min(40, filler_hits * 8)
            # Reward answers structured into multiple reasonably-sized sentences;
            # penalize one giant run-on sentence or extremely choppy fragments.
            if 8 <= avg_sentence_len <= 30:
                structure_score = 100
            elif avg_sentence_len < 8:
                structure_score = 70
            else:
                structure_score = 60
            clarity_score = round(max(0.0, structure_score - filler_penalty), 2)

        overall = round(
            self.KEYWORD_WEIGHT * keyword_score
            + self.COMPLETENESS_WEIGHT * completeness_score
            + self.CLARITY_WEIGHT * clarity_score,
            2,
        )

        feedback_parts = []
        if word_count == 0:
            feedback_parts.append("No answer was submitted.")
        else:
            if missed:
                feedback_parts.append(
                    "Consider mentioning: " + ", ".join(missed) + "."
                )
            if word_count < question.min_words:
                feedback_parts.append(
                    f"Your answer is quite short ({word_count} words). "
                    f"Aim for at least {question.min_words} words to fully explain your reasoning."
                )
            if clarity_score < 60:
                feedback_parts.append(
                    "Try to structure your answer into clear, complete sentences and avoid filler words."
                )
            if overall >= 85:
                feedback_parts.append("Strong answer overall.")
        feedback = " ".join(feedback_parts) if feedback_parts else "Solid answer."

        return {
            "keyword_coverage_score": keyword_score,
            "completeness_score": completeness_score,
            "clarity_score": clarity_score,
            "overall_score": overall,
            "matched_keywords": matched,
            "missed_keywords": missed,
            "feedback": feedback,
        }


class ClaudeEvaluator(BaseEvaluator):
    """
    Stub for LLM-based grading via the Anthropic API. Not wired to network
    calls in this build (no API key management here) -- shown as the
    extension point. To activate: implement `evaluate()` to call the
    Anthropic Messages API with a grading prompt that returns the same
    dict shape as RuleBasedEvaluator, then set EVALUATION_ENGINE="claude".
    """

    def evaluate(self, question, answer_text: str) -> dict:
        raise NotImplementedError(
            "ClaudeEvaluator is a placeholder. Implement the API call and "
            "return the same dict shape as RuleBasedEvaluator before enabling."
        )


def get_evaluator() -> BaseEvaluator:
    from django.conf import settings

    engine = getattr(settings, "EVALUATION_ENGINE", "rule_based")
    if engine == "rule_based":
        return RuleBasedEvaluator()
    if engine == "claude":
        return ClaudeEvaluator()
    raise ValueError(f"Unknown EVALUATION_ENGINE: {engine}")
