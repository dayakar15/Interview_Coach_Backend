from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationTests(APITestCase):
    def test_register_creates_user_with_hashed_password(self):
        url = reverse("register")
        resp = self.client.post(url, {
            "username": "alice", "email": "alice@example.com",
            "password": "StrongPass123!", "target_role": "backend",
            "experience_level": "mid",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        user = User.objects.get(username="alice")
        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_register_rejects_weak_password(self):
        url = reverse("register")
        resp = self.client.post(url, {
            "username": "bob", "email": "bob@example.com", "password": "123",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username="carol", password="StrongPass123!")
        resp = self.client.post(reverse("register"), {
            "username": "carol", "email": "c2@example.com", "password": "AnotherPass123!",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAndProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dave", password="StrongPass123!", email="dave@example.com"
        )

    def test_login_returns_jwt_tokens(self):
        resp = self.client.post(reverse("login"), {
            "username": "dave", "password": "StrongPass123!",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_rejects_wrong_password(self):
        resp = self.client.post(reverse("login"), {
            "username": "dave", "password": "wrong",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_requires_auth(self):
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_authenticated_user(self):
        login = self.client.post(reverse("login"), {
            "username": "dave", "password": "StrongPass123!",
        })
        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "dave")
