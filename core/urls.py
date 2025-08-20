from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from apps.base.views import base_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('base/', base_view, name='base'),
    path('', include('pages.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    