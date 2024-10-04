from django.contrib.auth import get_user_model
from django.urls import path, include
from .views import LogoutView, RegisterView, CustomTokenVerifyView, CustomTokenObtainPairView
User = get_user_model()


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_refresh'),
    path('verify/', CustomTokenVerifyView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
