from django.db import models
from ecommerce.models import Product, Category
from django.contrib.auth import get_user_model
User = get_user_model()


class ShippingInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'shipping infos'

    def __str__(self):
        return f'Shipping info for {self.user}'


