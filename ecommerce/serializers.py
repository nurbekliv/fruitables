# serializers.py
from rest_framework import serializers
from .models import Review, Product, LikedReview, ProductSales, Category


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


class ProductSalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSales
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
