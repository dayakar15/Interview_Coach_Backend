from rest_framework import serializers
from .models import Question, InterviewSession, SessionQuestion, Answer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        # Deliberately exclude expected_keywords/ideal_answer from what the
        # candidate sees -- that's the answer key, not the question.
        fields = ["id", "text", "category", "difficulty"]


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text", "submitted_at"]
        read_only_fields = ["id", "submitted_at"]


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        from evaluation.models import Evaluation
        model = Evaluation
        fields = [
            "keyword_coverage_score", "completeness_score", "clarity_score",
            "overall_score", "matched_keywords", "missed_keywords", "feedback",
        ]


class SessionQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    answer = AnswerSerializer(read_only=True)
    evaluation = EvaluationSerializer(read_only=True)

    class Meta:
        model = SessionQuestion
        fields = ["id", "order", "question", "answer", "evaluation"]


class InterviewSessionSerializer(serializers.ModelSerializer):
    session_questions = SessionQuestionSerializer(many=True, read_only=True)
    average_score = serializers.ReadOnlyField()

    class Meta:
        model = InterviewSession
        fields = [
            "id", "category", "status", "started_at", "completed_at",
            "average_score", "session_questions",
        ]
        read_only_fields = ["status", "started_at", "completed_at"]


class StartSessionSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=Question.CATEGORY_CHOICES, required=False, allow_blank=True, default=""
    )
    num_questions = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)


class SubmitAnswerSerializer(serializers.Serializer):
    session_question_id = serializers.IntegerField()
    text = serializers.CharField(allow_blank=True)
