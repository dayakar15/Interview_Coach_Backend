"""
Static knowledge base mapping category -> topics/resources to study.
This is intentionally simple data, not logic -- swap or extend this dict
(or load it from the DB/CMS) without touching the recommendation engine
in services.py.
"""

CATEGORY_RECOMMENDATIONS = {
    "dsa": {
        "topics": [
            "Big-O complexity analysis",
            "Arrays & two-pointer techniques",
            "Hash maps and sets",
            "Trees and graph traversal (BFS/DFS)",
            "Dynamic programming fundamentals",
        ],
        "resources": [
            "NeetCode 150 practice list",
            "CLRS Introduction to Algorithms (relevant chapters)",
            "LeetCode: filter by the category's weak topic and difficulty",
        ],
    },
    "system_design": {
        "topics": [
            "Load balancing & horizontal scaling",
            "Caching strategies (write-through, write-back, TTL)",
            "Database sharding & replication",
            "CAP theorem trade-offs",
            "API design & rate limiting",
        ],
        "resources": [
            "\"System Design Interview\" by Alex Xu",
            "ByteByteGo system design primers",
            "Practice: design a URL shortener / rate limiter / chat system",
        ],
    },
    "databases": {
        "topics": [
            "Normalization vs denormalization",
            "Indexing strategies and query plans",
            "Transactions & isolation levels",
            "SQL vs NoSQL trade-offs",
        ],
        "resources": [
            "Use EXPLAIN/ANALYZE on your own queries",
            "PostgreSQL official docs on indexing",
        ],
    },
    "behavioral": {
        "topics": [
            "STAR method structuring (Situation, Task, Action, Result)",
            "Conflict resolution stories",
            "Ownership & impact framing",
        ],
        "resources": [
            "Write out 5 STAR stories from past projects and rehearse aloud",
            "\"Cracking the PM/Coding Interview\" behavioral chapters",
        ],
    },
    "backend": {
        "topics": [
            "REST API design and status codes",
            "Authentication & authorization (JWT/OAuth)",
            "Idempotency and error handling",
            "Background jobs and queues",
        ],
        "resources": [
            "Build a small REST API and add auth + rate limiting to it",
            "Django/DRF or FastAPI official docs",
        ],
    },
    "frontend": {
        "topics": [
            "Component state management",
            "Rendering performance and re-renders",
            "Accessibility basics",
        ],
        "resources": [
            "React official docs -- hooks section",
            "web.dev performance guides",
        ],
    },
    "devops": {
        "topics": [
            "CI/CD pipeline design",
            "Containers & orchestration basics (Docker/Kubernetes)",
            "Monitoring, logging, and alerting",
        ],
        "resources": [
            "Docker & Kubernetes official getting-started guides",
            "Build a CI pipeline for a toy repo",
        ],
    },
}


def get_recommendations(category: str) -> dict:
    return CATEGORY_RECOMMENDATIONS.get(category, {"topics": [], "resources": []})
