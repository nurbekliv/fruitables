from django.urls import path
from .views import (get_reviews, post_reviews, put_reviews, delete_reviews,
                    DiscountView, LastJoinedProductView, AddToLikedView, ProductDetailView,
                    ProductFilterView, RecommendedProductsView, CategoryListView, BestSellerAPIView)

urlpatterns = [
    path('reviews/', post_reviews, name='post_reviews'),
    path('reviews/<int:product_id>/', put_reviews, name='put_reviews'),
    path('reviews/<int:pk>/delete/', delete_reviews, name='delete_reviews'),
    path('reviews/filter/', get_reviews, name='get_reviews'),
    path('discount/', DiscountView.as_view(), name='discount'),
    path('last_joined/', LastJoinedProductView.as_view(), name='last_joined'),
    path('comment/add_to_liked/', AddToLikedView.as_view(), name='add_to_liked'),
    path('detail/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('filter/', ProductFilterView.as_view(), name='product_filter'),
    path('recommended/', RecommendedProductsView.as_view(), name='recommended_products'),
    path('category/', CategoryListView.as_view(), name='category_list'),
    path('best_seller/', BestSellerAPIView.as_view(), name='best_seller'),
]
