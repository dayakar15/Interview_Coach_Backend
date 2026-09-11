from .engines import get_evaluator
from .models import Evaluation


def evaluate_answer(session_question) -> Evaluation:
    """
    Runs the configured evaluator against a SessionQuestion's answer and
    persists an Evaluation. Idempotent-ish: if called twice, updates the
    existing Evaluation rather than erroring on the OneToOne constraint.
    """
    answer = session_question.answer
    evaluator = get_evaluator()
    result = evaluator.evaluate(session_question.question, answer.text)

    evaluation, _created = Evaluation.objects.update_or_create(
        session_question=session_question,
        defaults={
            "keyword_coverage_score": result["keyword_coverage_score"],
            "completeness_score": result["completeness_score"],
            "clarity_score": result["clarity_score"],
            "overall_score": result["overall_score"],
            "matched_keywords": result["matched_keywords"],
            "missed_keywords": result["missed_keywords"],
            "feedback": result["feedback"],
            "engine": "rule_based",
        },
    )
    return evaluation
