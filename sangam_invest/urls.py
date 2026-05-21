from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sangam.urls')),
    path('accounts/', include('accounts.urls')),
    path('passbook/', include('passbook.urls')),
    # path('payments/', include('payments.urls')),
    # path('attendance/', include('attendance.urls')),
    # path('auditlogs/', include('auditlogs.urls')),
    # path('notifications/', include('notifications.urls')),
    # path('reports/', include('reports.urls')),

    
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
