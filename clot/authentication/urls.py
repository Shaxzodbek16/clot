from django.urls import path

from .views import (
    AuthView,
    UserDetailsView,
    LogoutView,
    LogoutAllView,
    TokenRefreshView,
)

urlpatterns = [
    path("user/<str:action>/", AuthView.as_view(), name="auth"),
    path("users/<str:slug>/", UserDetailsView.as_view(), name="user-detail"),
    path("users/", UserDetailsView.as_view(), name="user-list"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout/all/", LogoutAllView.as_view(), name="logout-all"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
