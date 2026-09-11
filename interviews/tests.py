from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Question

User = get_user_model()


class SessionLifecycleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="erin", password="StrongPass123!")
        login = self.client.post(reverse("login"), {"username": "erin", "password": "StrongPass123!"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        for i in range(4):
            Question.objects.create(
                text=f"DSA question {i}", category="dsa", difficulty="easy",
                expected_keywords=["sorted", "logarithmic"], min_words=10,
            )
        for i in range(3):
            Question.objects.create(
                text=f"Behavioral question {i}", category="behavioral", difficulty="easy",
                expected_keywords=["result"], min_words=10,
            )

    def test_cannot_start_session_without_auth(self):
        self.client.credentials()
        resp = self.client.post(reverse("session-list-create"), {})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start_session_picks_requested_category_and_count(self):
        resp = self.client.post(reverse("session-list-create"), {"category": "dsa", "num_questions": 3})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(len(resp.data["session_questions"]), 3)
        for sq in resp.data["session_questions"]:
            self.assertEqual(sq["question"]["category"], "dsa")

    def test_start_session_rejects_category_with_no_questions(self):
        resp = self.client.post(reverse("session-list-create"), {"category": "devops", "num_questions": 3})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_answer_hides_expected_keywords_from_candidate(self):
        create_resp = self.client.post(reverse("session-list-create"), {"category": "dsa", "num_questions": 1})
        self.assertNotIn("expected_keywords", create_resp.data["session_questions"][0]["question"])

    def test_submit_answer_creates_evaluation(self):
        create_resp = self.client.post(reverse("session-list-create"), {"category": "dsa", "num_questions": 1})
        session_id = create_resp.data["id"]
        sq_id = create_resp.data["session_questions"][0]["id"]

        answer_resp = self.client.post(
            reverse("session-answer", args=[session_id]),
            {"session_question_id": sq_id, "text": "Because it is sorted, the search is logarithmic."},
        )
        self.assertEqual(answer_resp.status_code, status.HTTP_200_OK, answer_resp.data)
        self.assertIsNotNone(answer_resp.data["evaluation"])
        self.assertGreater(answer_resp.data["evaluation"]["overall_score"], 0)

    def test_resubmitting_answer_updates_evaluation_not_duplicates(self):
        create_resp = self.client.post(reverse("session-list-create"), {"category": "dsa", "num_questions": 1})
        session_id = create_resp.data["id"]
        sq_id = create_resp.data["session_questions"][0]["id"]
        url = reverse("session-answer", args=[session_id])

        self.client.post(url, {"session_question_id": sq_id, "text": "short"})
        second = self.client.post(url, {"session_question_id": sq_id, "text": "A much longer and more thoughtful sorted logarithmic answer here."})

        from evaluation.models import Evaluation
        self.assertEqual(Evaluation.objects.filter(session_question_id=sq_id).count(), 1)
        self.assertGreater(second.data["evaluation"]["overall_score"], 0)

    def test_cannot_answer_another_users_session(self):
        create_resp = self.client.post(reverse("session-list-create"), {"category": "dsa", "num_questions": 1})
        session_id = create_resp.data["id"]
        sq_id = create_resp.data["session_questions"][0]["id"]

        other = User.objects.create_user(username="frank", password="StrongPass123!")
        login = self.client.post(reverse("login"), {"username": "frank", "password": "StrongPass123!"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        resp = self.client.post(
            reverse("session-answer", args=[session_id]),
            {"session_question_id": sq_id, "text": "trying to answer someone else's session"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_session_marks_status_and_returns_plan(self):
        create_resp = self.client.post(reverse("session-list-create"), {"category": "dsa", "num_questions": 1})
        session_id = create_resp.data["id"]
        sq_id = create_resp.data["session_questions"][0]["id"]
        self.client.post(
            reverse("session-answer", args=[session_id]),
            {"session_question_id": sq_id, "text": "weak"},
        )
        complete_resp = self.client.post(reverse("session-complete", args=[session_id]))
        self.assertEqual(complete_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(complete_resp.data["session"]["status"], "completed")
        self.assertIsNotNone(complete_resp.data["study_plan"])
