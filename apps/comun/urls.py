from django.urls import path

from . import views

app_name = "comun"

urlpatterns = [
    path("", views.salud, name="salud"),
    path("db/", views.salud_db, name="salud_db"),
]
