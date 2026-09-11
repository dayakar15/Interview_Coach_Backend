"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    """
    There's no frontend yet, so hitting '/' in a browser used to 404 with
    no explanation. This just points people to the real endpoints instead.
    """
    return JsonResponse({
        "message": "AI Interview Coach API is running.",
        "admin": "/admin/",
        "auth": {
            "register": "/api/auth/register/",
            "login": "/api/auth/login/",
            "refresh": "/api/auth/login/refresh/",
            "profile": "/api/auth/profile/",
        },
        "interviews": {
            "sessions": "/api/interviews/sessions/",
            "answer": "/api/interviews/sessions/<id>/answer/",
            "complete": "/api/interviews/sessions/<id>/complete/",
        },
        "studyplan": {
            "weak_areas": "/api/studyplan/weak-areas/",
            "plan": "/api/studyplan/plan/",
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/interviews/', include('interviews.urls')),
    path('api/studyplan/', include('studyplan.urls')),
]
