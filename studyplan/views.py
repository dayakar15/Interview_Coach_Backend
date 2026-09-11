from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WeakArea, StudyPlan
from .serializers import WeakAreaSerializer, StudyPlanSerializer
from .services import refresh_weak_areas_and_plan


class WeakAreaListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        areas = WeakArea.objects.filter(user=request.user).order_by("average_score")
        return Response(WeakAreaSerializer(areas, many=True).data)


class StudyPlanView(APIView):
    """GET returns the current plan; POST forces a recompute (useful after
    manual data changes or for a "refresh my plan" button in the UI)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            plan = request.user.study_plan
        except StudyPlan.DoesNotExist:
            plan = None
        if plan is None:
            return Response({"detail": "No study plan yet. Complete an interview session first."}, status=404)
        return Response(StudyPlanSerializer(plan).data)

    def post(self, request):
        plan = refresh_weak_areas_and_plan(request.user)
        if plan is None:
            return Response({"detail": "Not enough evaluated answers yet to build a plan."}, status=400)
        return Response(StudyPlanSerializer(plan).data)
