from django.contrib import admin
from .models import Category, Product, PriceHistory, ProductImage, Review, ProductSales, LikedReview

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(PriceHistory)
admin.site.register(ProductImage)
admin.site.register(Review)
admin.site.register(ProductSales)
admin.site.register(LikedReview)
