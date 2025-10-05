from django.urls import path
from . import views

app_name = 'product_qr'

urlpatterns = [
    path('', views.index, name='index'),
    path('view/<uuid:uuid>/', views.view_product, name='view_product'),
]
