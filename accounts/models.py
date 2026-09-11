from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. We extend AbstractUser (keeps username/email/password
    and Django's battle-tested auth machinery) instead of AbstractBaseUser,
    since we don't need to redesign the identity fields -- just add
    interview-coach-specific profile data.
    """

    TARGET_ROLE_CHOICES = [
        ("backend", "Backend Engineer"),
        ("frontend", "Frontend Engineer"),
        ("fullstack", "Full-Stack Engineer"),
        ("data", "Data Engineer / Scientist"),
        ("devops", "DevOps / SRE"),
        ("general", "General Software Engineer"),
    ]

    EXPERIENCE_CHOICES = [
        ("junior", "Junior (0-2 yrs)"),
        ("mid", "Mid (2-5 yrs)"),
        ("senior", "Senior (5+ yrs)"),
    ]

    target_role = models.CharField(
        max_length=20, choices=TARGET_ROLE_CHOICES, default="general"
    )
    experience_level = models.CharField(
        max_length=10, choices=EXPERIENCE_CHOICES, default="junior"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
