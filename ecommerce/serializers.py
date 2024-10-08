from rest_framework import serializers
from .models import Review, Product, LikedReview, Category, ProductImage, Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'comment', 'rating', 'created']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class LikedReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikedReview
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']


class OrderSerializer(serializers.Serializer):
    user = serializers.UUIDField()
    items = serializers.ListField(child=serializers.JSONField())

    def create(self, validated_data):
        items = validated_data.pop('items')

        # Order ni yaratish
        order = Order.objects.create(user=validated_data['user'])

        for item in items:
            product_id = item['product']

            # Product modelidan instansiyani olish
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with ID {product_id} does not exist")

            # Product modelining narxini itemga qo'shamiz
            item['price'] = product.price

            # 'product' kalitini item'dan o'chiramiz
            item.pop('product', None)

            # OrderItem yaratishda 'product'ga instansiyani beramiz
            OrderItem.objects.create(order=order, product=product, **item)

        # Faqat order va foydalanuvchi haqida ma'lumotni qaytaramiz
        return order





