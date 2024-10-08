from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated

from ecommerce.serializers import OrderSerializer
from .cart import Cart
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from ecommerce.models import Product, Order, OrderItem
from .serializers import PaymentSerializer
import stripe
from rest_framework.decorators import api_view
from .models import ShippingInfo
from .serializers import ShippingInfoSerializer
from django.conf import settings
from ecommerce.models import ProductImage
from django.contrib.auth import get_user_model

User = get_user_model()


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = Cart(request)
        total_price = cart.get_total_price(request)
        cart_len = cart.cart_len(request)
        keys = cart.get_product_keys(request)
        individual_price = {}
        product_image = {}
        for key in keys:
            individual_price[key] = cart.get_total(request, key)
            product_image[key] = ProductImage.objects.filter(product_id=key).first()
        cart = cart.get_cart_items(request)
        if cart_len == 0:
            return Response({'message': 'Savatcha bo\'sh'}, status=status.HTTP_200_OK)
        return Response({
            'cart': cart,
            'cart_len': cart_len,
            'total_price': total_price,
            'individual_price': individual_price,
            'product_image': product_image
        })


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.add_cart_item(request, product)
        cart_len = cart.cart_len(request)
        return Response({
            'cart_len': cart_len
        })


class CartRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        cart = Cart(request)
        cart.remove_cart_item(request, product_id)

        cart_len = cart.cart_len(request)
        total_price = cart.get_total_price(self.request)

        individual_prices = {key: cart.get_total(request, key) for key in cart.get_product_keys(request)}
        return Response({
            'cart_len': cart_len,
            'total_price': total_price,
            'individual_prices': individual_prices,
        })


class QuantityView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['plus', 'minus'],
                                         description='Mahsulot miqdorini oshirish yoki kamaytirish')
            },
            required=['action']
        ),
        operation_summary="Mahsulot miqdorini o'zgartirish/action formda keladi"
    )
    def patch(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)

        action = request.data.get('action')

        if action == 'plus':
            cart.add_cart_item(request, product)
        elif action == 'minus':
            cart.minus_cart_item(request, product)
        else:
            return Response({'error': 'Noto\'g\'ri action, "plus" yoki "minus" yuboring'},
                            status=status.HTTP_400_BAD_REQUEST)

        total_price = cart.get_total_price(request)
        cart_len = cart.cart_len(request)
        individual_prices = {key: cart.get_total(request, key) for key in cart.get_product_keys(request)}
        return Response({
            'success': True,
            'total_price': total_price,
            'cart_len': cart_len,
            'individual_prices': individual_prices
        }, status=status.HTTP_200_OK)


stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class ShippingInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: ShippingInfoSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        shipping_info = ShippingInfo.objects.filter(user=user).order_by('-created')[:3]
        serializer = ShippingInfoSerializer(shipping_info, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ShippingInfoSerializer,
        responses={201: ShippingInfoSerializer, 400: 'Bad Request'}
    )
    def post(self, request):
        serializer = ShippingInfoSerializer(data=request.data)

        if serializer.is_valid():
            existing_addresses = ShippingInfo.objects.filter(user=request.user)
            new_latitude = serializer.validated_data['latitude']
            new_longitude = serializer.validated_data['longitude']

            # Latitude va longitude takrorlansa, xato qaytaring
            if existing_addresses.filter(latitude=new_latitude, longitude=new_longitude).exists():
                return Response({'error': 'This address already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(user=request.user)  # Yangi manzilni saqlash
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=PaymentSerializer)
@api_view(['POST'])
def create_payment(request):
    serializer = PaymentSerializer(data=request.data)

    if serializer.is_valid():
        amount = serializer.validated_data['amount'] * 100  # Amount centlarda bo'lishi kerak
        currency = serializer.validated_data.get('currency', 'usd')
        token = serializer.validated_data['token']

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=token,
                description='Payment Charge'
            )
            return Response({'status': 'success', 'charge': charge}, status=status.HTTP_200_OK)

        except stripe.error.CardError as e:
            return Response({'error': 'Card was declined'}, status=status.HTTP_402_PAYMENT_REQUIRED)

        except stripe.error.RateLimitError as e:
            return Response({'error': 'Rate limit error, try again later'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        except stripe.error.InvalidRequestError as e:
            return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.AuthenticationError as e:
            return Response({'error': 'Authentication with Stripe failed'}, status=status.HTTP_403_FORBIDDEN)

        except stripe.error.APIConnectionError as e:
            return Response({'error': 'Network communication with Stripe failed'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except stripe.error.StripeError as e:
            return Response({'error': 'Stripe error, try again later'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=OrderSerializer,
        responses={201: OrderSerializer, 400: 'Bad Request'}
    )
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data)

        if serializer.is_valid():
            order = serializer.save(user=request.user)
            # Order obyekti uchun serializers yaratish
            return Response({
                'order_id': str(order.id),  # Yaratilgan order ID sini qaytaramiz
                'user': str(order.user),  # Yaratilgan order foydalanuvchisi
                'items': serializer.validated_data['items']  # Yaratilgan orderdagi buyurtmalar
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

