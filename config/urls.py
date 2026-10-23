from django.urls import path
from study import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("", views.library, name="library"),
    path("lessons/<slug:lesson_id>/<str:guide>/", views.lesson, name="lesson"),
]
