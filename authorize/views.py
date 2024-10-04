from django.contrib.auth import get_user_model
from .serializers import LogoutSerializer, RegisterSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import PasswordResetSerializer, PasswordResetConfirmSerializer

User = get_user_model()


class RegisterView(APIView):
    @swagger_auto_schema(tags=['auth'],
                         request_body=RegisterSerializer,
                         operation_summary="Foydalanuvchi qo'shish")
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            return Response({"msg": "User created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['auth'],
                         request_body=LogoutSerializer, operation_summary="Tizimdan chiqish")
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data["refresh"]
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_summary="Foydalanuvchini tizimga kirishi",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Foydalanuvchi emaili'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Foydalanuvchi paroli')
            },
        ),
        responses={200: 'Tokenlar muvaffaqiyatli olindi'}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):

    @swagger_auto_schema(
        tags=['auth'],
        operation_summary="Tokenni tasdiqlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING, description='Token')
            },
        ),
        responses={200: 'Token muvaffaqiyatli tasdiqlandi'}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# class PasswordResetAPIView(generics.GenericAPIView):
#     serializer_class = PasswordResetSerializer
#     permission_classes = [AllowAny]
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.get_user()
#         token = default_token_generator.make_token(user)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#
#         # Email yuborish
#         send_mail(
#             'Password Reset',
#             f'You can reset your password using the link: '
#             f'http://yourdomain.com/api/password_reset/confirm/?uid={uid}&token={token}',
#             'from@example.com',
#             [user.email],
#             fail_silently=False,
#         )
#         return Response({"detail": "Password reset email sent."}, status=status.HTTP_200_OK)
#
#
# class PasswordResetConfirmAPIView(generics.GenericAPIView):
#     serializer_class = PasswordResetConfirmSerializer
#     permission_classes = [AllowAny]
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)