from django.urls import path
from deals import views

app_name = 'deals'

urlpatterns = [
    path('', views.index, name='index'),
]
