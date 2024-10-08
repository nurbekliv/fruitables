from django.contrib.auth import get_user_model
from rest_framework.pagination import PageNumberPagination
from ecommerce.models import Order, OrderItem
from ecommerce.serializers import OrderSerializer
from .serializers import RegisterSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from ecommerce.models import PriceHistory, Order
from django.utils.encoding import force_str
from ecommerce.models import Product

User = get_user_model()


class RegisterView(APIView):
    @swagger_auto_schema(tags=['auth'],
                         request_body=RegisterSerializer,
                         operation_summary="Foydalanuvchi qo'shish")
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                name=serializer.validated_data['name'],
                password=serializer.validated_data['password']
            )
            return Response({"msg": "User created successfully."}, status=status.HTTP_201_CREATED)
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


class CustomTokenVerifyAPIView(APIView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_summary="Tokenni tasdiqlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Access token')
            },
        ),
        responses={
            200: 'Token muvaffaqiyatli tasdiqlandi',
            400: 'Token noto\'g\'ri yoki yaroqsiz',
        }
    )
    def post(self, request):
        token = request.data.get('access_token')

        if not token:
            return Response({"error": _("Tokenni kiriting")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = AccessToken(token)
            return Response({"message": _("Token muvaffaqiyatli tasdiqlandi")}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": _("Token tasdiqlashda xato: ") + str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['auth'], operation_summary="Parolni unitdingizmi", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description=_('Foydalanuvchi emaili')),
            },
        ), )
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({"error": _("Email manzilini kiriting")}, status=status.HTTP_400_BAD_REQUEST)

        # Email orqali foydalanuvchini qidiramiz
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": _("Bu email manzili bilan foydalanuvchi topilmadi.")},
                            status=status.HTTP_404_NOT_FOUND)

        # Parolni tiklash tokeni yaratish
        token_generator = default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # Foydalanuvchi ID'sini base64 formatga o'tkazamiz
        token = token_generator.make_token(user)  # Parolni tiklash tokenini yaratamiz

        # Tiklash linkini yaratish
        password_reset_url = f"{request.scheme}://{request.get_host()}/reset/confirm/?uid={uid}&token={token}"

        # Emailni yuborish
        subject = _("Parolni tiklash")
        message = _(
            f"Salom {user.username},\n\nParolingizni tiklash uchun quyidagi linkni bosing:\n{password_reset_url}\n\nAgar bu xabarni siz yubormagan bo'lsangiz, hech qanday harakat qilmang.")
        html_message = _(
            f"<p>Salom {user.username},</p><p>Parolingizni tiklash uchun quyidagi <a href='{password_reset_url}     '>link</a> ni bosing.</p><p>Agar bu xabarni siz yubormagan bo'lsangiz, hech qanday harakat qilmang.</p>")

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_message
        )

        return Response({"message": _("Parolni tiklash uchun link emailga jo'natildi.")}, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Foydalanuvchi tizimga kirgan bo'lishi kerak

    @swagger_auto_schema(
        tags=['auth'],
        operation_summary="Foydalanuvchini tizimdan chiqarish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
            },
        ),
        responses={
            200: 'Muvaffaqiyatli chiqildi',
            400: 'Token noto‘g‘ri',
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({"error": _("Refresh tokenni kiriting")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Refresh tokenni bloklash
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": _("Foydalanuvchi muvaffaqiyatli tizimdan chiqarildi.")},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": _("Tokenni bloklashda xato: ") + str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshAPIView(TokenRefreshView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_summary="Yangi Access token olish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='Yangi access token'),
                }
            ),
            400: 'Refresh token noto\'g\'ri yoki yaroqsiz',
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PasswordResetConfirmAPIView(APIView):
    @swagger_auto_schema(
        tags=['auth'],
        operation_summary="Parolni tiklash",
        manual_parameters=[
            openapi.Parameter('uid', openapi.IN_QUERY, description='Foydalanuvchi ID', type=openapi.TYPE_STRING,
                              required=True),
            openapi.Parameter('token', openapi.IN_QUERY, description='Tiklash tokeni', type=openapi.TYPE_STRING,
                              required=True),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Yangi parol'),
            },
        ),
        responses={
            200: 'Parol muvaffaqiyatli yangilandi',
            400: 'Noto\'g\'ri token yoki UID',
        }
    )
    def post(self, request):
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response({"error": _("Barcha maydonlarni to'ldiring.")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # UID'ni decode qilib, foydalanuvchi ID'sini olish
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)

            # Tokenni tasdiqlash
            if not default_token_generator.check_token(user, token):
                return Response({"error": _("Noto'g'ri token yoki UID.")}, status=status.HTTP_400_BAD_REQUEST)

            # Yangi parolni o'rnatish
            user.set_password(new_password)
            user.save()

            return Response({"message": _("Parol muvaffaqiyatli yangilandi.")}, status=status.HTTP_200_OK)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": _("Noto'g'ri token yoki UID.")}, status=status.HTTP_400_BAD_REQUEST)


class CustomPagination(PageNumberPagination):
    page_size = 1  # Har bir sahifada nechta buyurtma ko'rsatish
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination  # Sahifalash classini qo'shamiz

    @swagger_auto_schema(
        operation_description="Foydalanuvchining buyurtmalarini ko'rish",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Sahifa raqami", type=openapi.TYPE_INTEGER, required=True),
        ]
    )
    def get(self, request):
        user = request.user
        # Buyurtmalarni teskari tartibda olish
        orders = Order.objects.filter(user_id=user.id).order_by('-created')  # Eng oxirgi buyurtmalarni birinchi ko'rsatish

        paginator = self.pagination_class()  # Sahifalashni ishlatish
        page = paginator.paginate_queryset(orders, request)  # Buyurtmalarni sahifalash

        # Buyurtmalar uchun itemlar yaratish
        items = []
        for order in page:
            order_items = OrderItem.objects.filter(order_id=order.id).select_related('product')

            item_list = []
            for item in order_items:
                item_list.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'price': item.price,
                    'quantity': item.quantity,
                })

            items.append({
                'order_id': order.id,
                'created_at': order.created,
                'items': item_list
            })

        # Sahifalangan javobni qaytarish
        return paginator.get_paginated_response(items)
