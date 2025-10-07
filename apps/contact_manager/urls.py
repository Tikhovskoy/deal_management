from django.urls import path

from . import views

app_name = "contact_manager"

urlpatterns = [
    path("", views.index, name="index"),
    path("export/", views.export_contacts, name="export_contacts"),
    path("import/", views.import_contacts, name="import_contacts"),
]
