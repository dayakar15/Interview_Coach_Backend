from django.urls import path
from .views import SessionListCreateView, SessionDetailView, SubmitAnswerView, CompleteSessionView

urlpatterns = [
    path("sessions/", SessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<int:pk>/", SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<int:session_id>/answer/", SubmitAnswerView.as_view(), name="session-answer"),
    path("sessions/<int:session_id>/complete/", CompleteSessionView.as_view(), name="session-complete"),
]
