from django.db.models import Sum, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from .models import Review, LikedReview, Category, ProductImage, OrderItem
from .serializers import ReviewSerializer, ProductSerializer, CategorySerializer, ProductImageSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from .models import Product
from .permissions import IsOwnerOrReadOnly, PurchasePermission


class ReviewPagination(PageNumberPagination):
    page_size = 3


@swagger_auto_schema(
    tags=['review'],
    method='get',
    manual_parameters=[
        openapi.Parameter('product_id', openapi.IN_QUERY, description="Product ID to filter reviews",
                          type=openapi.TYPE_INTEGER),
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number for pagination",
                          type=openapi.TYPE_INTEGER),
    ],
    responses={200: ReviewSerializer(many=True)}  # Bu qism o'zgartirilishi kerak
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrReadOnly])
def get_reviews(request):
    product_id = request.query_params.get('product_id')

    if product_id:
        try:
            product_id = int(product_id)
        except ValueError:
            return Response({'error': 'Invalid product_id format'}, status=status.HTTP_400_BAD_REQUEST)

        # LikedReview modelda bor izohlar (like soniga teskari tartibda)
        liked_review_objects = (Review.objects
                                .filter(likedreview__isnull=False, product__id=product_id)
                                .annotate(like_count=Count('likedreview'))  # Like sonini hisoblaymiz
                                .order_by('-like_count', '-created'))  # Like soni teskari tartibda

        # LikedReview modelda yo'q izohlar (like bosilmagan)
        not_liked_review_objects = (Review.objects
                                    .filter(likedreview__isnull=True, product__id=product_id)
                                    .order_by('-created'))

        # Ikkala querysetni birlashtiramiz, paginatsiya qilish uchun ro'yxat shakliga o'tkazamiz
        combined_reviews = list(liked_review_objects) + list(not_liked_review_objects)

        # Paginatsiya
        paginator = ReviewPagination()
        paginated_reviews = paginator.paginate_queryset(combined_reviews, request)

        # Serializatsiya qilish
        serialized_reviews = ReviewSerializer(paginated_reviews, many=True).data

        # Paginatsiyalangan javobni qaytarish
        return paginator.get_paginated_response(serialized_reviews)

    else:
        return Response({'error': 'product_id not found'}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    tags=['review'],
    method='post',
    request_body=ReviewSerializer,
    responses={201: ReviewSerializer, 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrReadOnly, PurchasePermission])
def post_reviews(request):
    serializer = ReviewSerializer(data=request.data)

    if serializer.is_valid():
        # Sharh foydalanuvchi bilan saqlanadi
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# PUT: Update an existing review
@swagger_auto_schema(
    tags=['review'],
    method='put',
    request_body=ReviewSerializer,
    responses={200: ReviewSerializer, 400: 'Bad Request', 404: 'Not Found'}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsOwnerOrReadOnly])
def put_reviews(request, product_id):
    try:
        review = Review.objects.get(pk=product_id)
    except Review.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ReviewSerializer(review, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# DELETE: Delete a review
@swagger_auto_schema(
    tags=['review'],
    method='delete',
    responses={204: 'No Content', 404: 'Not Found'}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsOwnerOrReadOnly])
def delete_reviews(request, pk):
    try:
        review = Review.objects.get(pk=pk)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Review.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


class DiscountView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        products = Product.objects.filter(discount__gt=0)
        product_data = []

        for product in products:
            product_images = ProductImage.objects.filter(product_id=product.id)
            images_data = ProductImageSerializer(product_images, many=True).data

            product_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'discount': product.discount,
                'images': images_data,  # Rasmlarni qo'shamiz
            })

        return Response(product_data)


class LastJoinedProductView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        products = Product.objects.order_by('-created')[:10]
        product_data = []

        for product in products:
            product_images = ProductImage.objects.filter(product_id=product.id)
            images_data = ProductImageSerializer(product_images, many=True).data

            product_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'created': product.created,
                'images': images_data,  # Rasmlarni qo'shamiz
            })

        return Response(product_data)


class AddToLikedView(APIView):
    permission_classes = [IsAuthenticated, PurchasePermission]

    @swagger_auto_schema(tags=['product'], request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        'review_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Review ID'),
        'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID')
    }))
    def post(self, request):
        review_id = request.data.get('review_id')
        product_id = request.data.get('product_id')
        user = request.user

        if review_id is None or product_id is None:
            return Response({'error': 'Review ID and Product ID are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            review = Review.objects.get(id=review_id)
            product = Product.objects.get(id=product_id)  # Mahsulotni olish

            # LikedReview yaratish yoki o'chirish
            liked = LikedReview.toggle_like(user, review, product)

            if liked:
                return Response({'message': 'Review added to liked successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Review removed from liked successfully'}, status=status.HTTP_200_OK)

        except Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
            if product.views is None:
                product.views = 0
            product.views += 1
            product.save()

            product_images = ProductImage.objects.filter(product_id=product.id)
            product_data = ProductSerializer(product).data
            product_data['images'] = ProductImageSerializer(product_images, many=True).data

            return Response(product_data, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductFilterView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['product'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY,
                              description="Mahsulot kategoriyasi", type=openapi.TYPE_STRING)
        ],
        responses={200: ProductSerializer(many=True)}
    )
    def get(self, request):
        category = request.GET.get('category')
        products = Product.objects.filter(category__name=category)

        if products.count() == 0:
            return Response({'message': 'Bu kategoriyada mahsulot yo\'q'}, status=status.HTTP_404_NOT_FOUND)

        product_data = []
        for product in products:
            product_images = ProductImage.objects.filter(product_id=product.id)
            images_data = ProductImageSerializer(product_images, many=True).data

            product_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'images': images_data,
            })

        return Response(product_data)


class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class RecommendedProductsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        categories = ['top', 'apple', 'rolex', 'daily']
        filtered_products = {}

        for category in categories:
            products = Product.objects.filter(category__name=category)[:8]
            product_data = []

            for product in products:
                product_images = ProductImage.objects.filter(product_id=product.id)
                images_data = ProductImageSerializer(product_images, many=True).data

                product_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'images': images_data,
                })

            filtered_products[category] = product_data

        return Response(filtered_products)


class BestSellerAPIView(APIView):
    def get(self, request):
        # Eng ko'p odam sotib olgan mahsulotlarni hisoblash
        best_sellers = (
            OrderItem.objects
            .values('product_id')
            .annotate(total_orders=Count('order__user', distinct=True))
            .order_by('-total_orders', '-quantity')[:10]
        )

        # Mahsulotlarni olish
        product_ids = [item['product_id'] for item in best_sellers]
        products = Product.objects.filter(id__in=product_ids)

        # Mahsulotlar va buyurtma sonini serializatsiya qilish
        serialized_products = ProductSerializer(products, many=True).data

        # Natijani birlashtirish
        result = [
            {
                'product': serialized_product,
                'total_orders': next(item['total_orders'] for item in best_sellers if item['product_id'] == serialized_product['id'])
            }
            for serialized_product in serialized_products
        ]

        return Response(result, status=status.HTTP_200_OK)