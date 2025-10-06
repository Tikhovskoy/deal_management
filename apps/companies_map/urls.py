from django.urls import path
from . import views

app_name = 'companies_map'

urlpatterns = [
    path('', views.index, name='index'),
]
