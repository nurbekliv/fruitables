from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = RichTextUploadingField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    discount = models.IntegerField(default=0)
    rating = models.FloatField(default=0)
    views = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'products'

    def save(self, *args, **kwargs):
        if self.pk:
            original = Product.objects.get(pk=self.pk)
            if original.price != self.price:
                PriceHistory.objects.create(product=self, price=original.price)
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'price histories'

    def __str__(self):
        return f'{self.product.name} - {self.price}'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/product_images')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'product images'

    def __str__(self):
        return f'Image of {self.product.name}'


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.PositiveSmallIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'reviews'

    def __str__(self):
        return f'Review of {self.product.name} by {self.user}'

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError('Rating must be between 1 and 5.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class LikedReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Mahsulotga referens
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'liked reviews'
        unique_together = ('user', 'review')  # Foydalanuvchi va sharh kombinatsiyasida noyoblik

    def __str__(self):
        return f'{self.review} liked by {self.user}'

    @classmethod
    def toggle_like(cls, user, review, product):
        # Foydalanuvchi tomonidan like mavjudligini tekshirish
        liked_review = cls.objects.filter(user=user, review=review, product=product).first()
        if liked_review:
            # Agar like mavjud bo'lsa, uni o'chirish
            liked_review.delete()
            return False  # Like o'chirildi
        else:
            # Agar like mavjud bo'lmasa, yangi like qo'shish
            cls.objects.create(user=user, review=review, product=product)
            return True  # Like qo'shildi


class ProductSales(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'solded products'

    def __str__(self):
        return f'Solded product by {self.user}'