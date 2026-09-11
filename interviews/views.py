import random
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from evaluation.services import evaluate_answer
from studyplan.services import refresh_weak_areas_and_plan
from .models import Question, InterviewSession, SessionQuestion, Answer
from .serializers import (
    InterviewSessionSerializer, StartSessionSerializer, SubmitAnswerSerializer,
)


class SessionListCreateView(generics.ListCreateAPIView):
    """
    GET: list the current user's sessions.
    POST: start a new session -- picks `num_questions` active questions
    (optionally filtered by category) in random order and attaches them.
    """
    serializer_class = InterviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user).order_by("-started_at")

    def create(self, request, *args, **kwargs):
        params = StartSessionSerializer(data=request.data)
        params.is_valid(raise_exception=True)
        category = params.validated_data.get("category", "")
        num_questions = params.validated_data["num_questions"]

        qs = Question.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)

        available = list(qs)
        if not available:
            return Response(
                {"detail": "No questions available for this category."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chosen = random.sample(available, k=min(num_questions, len(available)))

        session = InterviewSession.objects.create(user=request.user, category=category)
        for i, q in enumerate(chosen, start=1):
            SessionQuestion.objects.create(session=session, question=q, order=i)

        out = InterviewSessionSerializer(session)
        return Response(out.data, status=status.HTTP_201_CREATED)


class SessionDetailView(generics.RetrieveAPIView):
    serializer_class = InterviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user)


class SubmitAnswerView(APIView):
    """
    POST /api/interviews/sessions/<id>/answer/
    Creates (or replaces) the Answer for a SessionQuestion in this session,
    then immediately evaluates it and returns the score/feedback. Evaluating
    synchronously is fine for our rule-based engine (microseconds); if the
    Claude engine is enabled later, this is the spot to move to a background
    task (Celery) so the request doesn't block on an LLM call.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(InterviewSession, pk=session_id, user=request.user)
        payload = SubmitAnswerSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        sq = get_object_or_404(
            SessionQuestion, pk=payload.validated_data["session_question_id"], session=session
        )

        Answer.objects.update_or_create(
            session_question=sq, defaults={"text": payload.validated_data["text"]}
        )
        evaluation = evaluate_answer(sq)

        from .serializers import SessionQuestionSerializer
        return Response(SessionQuestionSerializer(sq).data, status=status.HTTP_200_OK)


class CompleteSessionView(APIView):
    """
    Marks a session completed, then triggers weak-area detection and
    study-plan (re)generation for the user. This is the integration point
    between the "interviewing" domain and the "coaching" domain.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(InterviewSession, pk=session_id, user=request.user)
        if session.status != "completed":
            session.status = "completed"
            session.completed_at = timezone.now()
            session.save(update_fields=["status", "completed_at"])

        plan = refresh_weak_areas_and_plan(request.user)

        from studyplan.serializers import StudyPlanSerializer
        return Response(
            {
                "session": InterviewSessionSerializer(session).data,
                "study_plan": StudyPlanSerializer(plan).data if plan else None,
            }
        )
