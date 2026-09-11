from django.urls import path
from .views import WeakAreaListView, StudyPlanView

urlpatterns = [
    path("weak-areas/", WeakAreaListView.as_view(), name="weak-areas"),
    path("plan/", StudyPlanView.as_view(), name="study-plan"),
]
