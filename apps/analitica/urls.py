from django.urls import path

from . import views

app_name = "analitica"

urlpatterns = [
    path("", views.PanelView.as_view(), name="inicio"),
]
