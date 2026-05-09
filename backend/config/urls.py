"""
URL configuration for Smart Campus Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/scheduler/', include('apps.scheduler.urls')),
    path('api/communication/', include('apps.communication.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
