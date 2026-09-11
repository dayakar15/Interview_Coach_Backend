from django.core.management.base import BaseCommand
from interviews.models import Question

QUESTIONS = [
    dict(category="dsa", difficulty="easy",
         text="What is the time complexity of binary search, and why?",
         expected_keywords=["logarithmic", "log n", "sorted", "divide"],
         min_words=20),
    dict(category="dsa", difficulty="medium",
         text="Explain the difference between a hash map and a binary search tree, including their time complexities.",
         expected_keywords=["hash", "o(1)", "tree", "o(log n)", "collision"],
         min_words=30),
    dict(category="dsa", difficulty="hard",
         text="How would you detect a cycle in a linked list, and what is the space complexity of your approach?",
         expected_keywords=["fast", "slow", "pointer", "cycle", "o(1) space"],
         min_words=30),
    dict(category="system_design", difficulty="medium",
         text="How would you design a URL shortening service like bit.ly?",
         expected_keywords=["hash", "database", "cache", "scale", "collision"],
         min_words=40),
    dict(category="system_design", difficulty="hard",
         text="Describe how you would design a rate limiter for an API used by millions of clients.",
         expected_keywords=["token bucket", "sliding window", "redis", "distributed"],
         min_words=40),
    dict(category="databases", difficulty="medium",
         text="What is database normalization and what problems does it solve?",
         expected_keywords=["redundancy", "normal form", "integrity", "anomalies"],
         min_words=25),
    dict(category="databases", difficulty="medium",
         text="Explain ACID properties in the context of relational databases.",
         expected_keywords=["atomicity", "consistency", "isolation", "durability"],
         min_words=30),
    dict(category="backend", difficulty="easy",
         text="What is the difference between PUT and PATCH in a REST API?",
         expected_keywords=["idempotent", "partial", "full", "replace"],
         min_words=20),
    dict(category="backend", difficulty="medium",
         text="How does JWT-based authentication work, and what are its trade-offs versus session-based auth?",
         expected_keywords=["token", "stateless", "signature", "expiry", "revoke"],
         min_words=35),
    dict(category="behavioral", difficulty="easy",
         text="Tell me about a time you disagreed with a teammate. How did you handle it?",
         expected_keywords=["disagreement", "listened", "compromise", "outcome"],
         min_words=40),
    dict(category="behavioral", difficulty="medium",
         text="Describe a project where you had to meet a tight deadline. What trade-offs did you make?",
         expected_keywords=["deadline", "prioritize", "trade-off", "result"],
         min_words=40),
    dict(category="devops", difficulty="medium",
         text="What is the purpose of a CI/CD pipeline, and what stages would you include for a typical web app?",
         expected_keywords=["build", "test", "deploy", "automation", "pipeline"],
         min_words=30),
    dict(category="frontend", difficulty="easy",
         text="What causes unnecessary re-renders in a React component, and how can you prevent them?",
         expected_keywords=["state", "props", "memo", "re-render", "key"],
         min_words=25),
]


class Command(BaseCommand):
    help = "Seed the database with sample interview questions."

    def handle(self, *args, **options):
        created = 0
        for q in QUESTIONS:
            _, was_created = Question.objects.get_or_create(
                text=q["text"],
                defaults={
                    "category": q["category"],
                    "difficulty": q["difficulty"],
                    "expected_keywords": q["expected_keywords"],
                    "min_words": q["min_words"],
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new questions (total in DB: {Question.objects.count()})."))
