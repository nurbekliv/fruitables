from django.urls import path
from .views import (CartView, CartAddView,
                    CartRemoveView, QuantityView, ShippingInfoView, create_payment, OrderCreateView)


urlpatterns = [
    path('', CartView.as_view()),
    path('add/<int:product_id>/', CartAddView.as_view()),
    path('remove/<int:product_id>/', CartRemoveView.as_view()),
    path('quantity/<int:product_id>/', QuantityView.as_view()),
    path('shipping_info/', ShippingInfoView.as_view(), name='shipping_info'),
    path('create_payment/', create_payment, name='create_payment'),
    path('order_create/', OrderCreateView.as_view(), name='order'),
]
