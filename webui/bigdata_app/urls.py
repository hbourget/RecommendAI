# pages/urls.py
from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.accueil_view, name="accueil"),
    path("accueil", views.accueil_view, name="accueil"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("dataset", views.dataset_view, name="dataset"),
]
