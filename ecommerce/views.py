from django.db.models import Sum, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from .models import Review, LikedReview, Category
from .serializers import ReviewSerializer, ProductSerializer, CategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from .models import Product
from ecommerce.models import ProductSales
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
def put_reviews(request, pk):
    try:
        review = Review.objects.get(pk=pk)
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


class BestSellerView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        best_seller = ProductSales.objects.values('product') \
                          .annotate(total_sold=Sum('quantity')) \
                          .order_by('-total_sold')[:10]

        best_seller_products = []
        for item in best_seller:
            try:
                product = Product.objects.get(id=item['product'])
                best_seller_products.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'total_sold': item['total_sold']
                })
            except Product.DoesNotExist:
                continue

        return Response({'best_seller_products': best_seller_products})


class DiscountView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        products = Product.objects.filter(discount__gt=0)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class LastJoindedProductView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'])
    def get(self, request):
        products = Product.objects.order_by('-created')[:10]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class BuyProductView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['product'], request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
        'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product quantity')
    }))
    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        if product_id and quantity:
            try:
                product = Product.objects.get(id=product_id)
                ProductSales.objects.create(user=request.user, product=product, quantity=quantity)
                return Response({'message': 'Product bought successfully'}, status=status.HTTP_200_OK)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Product ID and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)


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
            product.views += 1
            product.save()
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


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
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


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
            filtered_products[category] = Product.objects.filter(category__name=category)[:8]

        return Response(filtered_products)
