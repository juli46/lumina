from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path("accounts/", include("allauth.urls")),
]

# Servir archivos media también cuando DEBUG=False
urlpatterns += [
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {
            'document_root': settings.MEDIA_ROOT,
        }
    ),
]