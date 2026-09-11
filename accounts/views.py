from rest_framework import generics, permissions
from .serializers import RegisterSerializer, UserProfileSerializer


class RegisterView(generics.CreateAPIView):
    """
    Public endpoint. Login itself is handled by SimpleJWT's TokenObtainPairView
    (wired directly in config/urls.py) so we don't reinvent password checking.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
