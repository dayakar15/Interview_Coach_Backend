from rest_framework import serializers
from .models import WeakArea, StudyPlan, StudyPlanItem


class WeakAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeakArea
        fields = ["category", "average_score", "attempts", "is_weak", "updated_at"]


class StudyPlanItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPlanItem
        fields = [
            "category", "priority", "average_score",
            "recommended_topics", "recommended_resources", "practice_question_ids",
        ]


class StudyPlanSerializer(serializers.ModelSerializer):
    items = StudyPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model = StudyPlan
        fields = ["generated_at", "summary", "items"]
