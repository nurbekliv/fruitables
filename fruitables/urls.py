from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions



schema_view = get_schema_view(
    openapi.Info(
        title="Fruitables API",
        default_version='v1',
        description="API for Fruitables",
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authorize.urls')),
    path('cart/', include('cart.urls')),
    path('product/', include('ecommerce.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
