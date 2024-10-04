from django.urls import path
from .views import (get_reviews, post_reviews, put_reviews, delete_reviews, BestSellerView,
                    DiscountView, LastJoindedProductView, BuyProductView, AddToLikedView, ProductDetailView,
                    ProductFilterView, RecommendedProductsView, CategoryListView)

urlpatterns = [
    path('reviews/', post_reviews, name='post_reviews'),
    path('reviews/<int:pk>/', put_reviews, name='put_reviews'),
    path('reviews/<int:pk>/delete/', delete_reviews, name='delete_reviews'),
    path('reviews/filter/', get_reviews, name='get_reviews'),
    path('best_seller/', BestSellerView.as_view(), name='best_seller'),
    path('discount/', DiscountView.as_view(), name='discount'),
    path('last_joined/', LastJoindedProductView.as_view(), name='last_joined'),
    path('buy_product/', BuyProductView.as_view(), name='buy_product'),
    path('comment/add_to_liked/', AddToLikedView.as_view(), name='add_to_liked'),
    path('detail/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('filter/', ProductFilterView.as_view(), name='product_filter'),
    path('recommended/', RecommendedProductsView.as_view(), name='recommended_products'),
    path('category/', CategoryListView.as_view(), name='category_list'),
]
