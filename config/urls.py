from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from monitor.views import WebsiteViewSet, HealthCheckViewSet, AlertViewSet

router = DefaultRouter()
router.register(r'api/websites', WebsiteViewSet, basename='website')
router.register(r'api/health-checks', HealthCheckViewSet, basename='health-check')
router.register(r'api/alerts', AlertViewSet, basename='alert')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitor.urls')),
    path('', include(router.urls)),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api-auth/', include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
