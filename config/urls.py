from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.home.urls")),
    path("deals/", include("apps.deals.urls")),
    path("qr/", include("apps.product_qr.urls")),
    path("employees/", include("apps.employees.urls")),
    path("map/", include("apps.companies_map.urls")),
]
