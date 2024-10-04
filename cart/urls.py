from django.urls import path
from .views import (CartView, CartAddView,
                    CartRemoveView, QuantityView, create_payment, ShippingInfoView)


urlpatterns = [
    path('', CartView.as_view()),
    path('add/<int:product_id>/', CartAddView.as_view()),
    path('remove/<int:product_id>/', CartRemoveView.as_view()),
    path('quantity/<int:product_id>/', QuantityView.as_view()),
    path('create_payment/', create_payment, name='create_payment'),
    path('shipping_info/', ShippingInfoView.as_view(), name='shipping_info'),
]
