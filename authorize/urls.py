from django.contrib.auth import get_user_model
from django.urls import path, include
from .views import (LogoutAPIView, RegisterView, CustomTokenVerifyAPIView, CustomTokenObtainPairView,
                    PasswordResetAPIView, CustomTokenRefreshAPIView, PasswordResetConfirmAPIView, ProfileAPIView)

User = get_user_model()

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_refresh'),
    path('verify/', CustomTokenVerifyAPIView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('password_reset/', PasswordResetAPIView.as_view(), name='password_reset'),
    path('api/token/refresh/', CustomTokenRefreshAPIView.as_view(), name='token_refresh'),
    path('reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
]
