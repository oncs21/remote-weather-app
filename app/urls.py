from django.urls import path
from . import views

urlpatterns = [
    path("", views.weatherView, name="home"),
    path("docs/<str:contentFile>", views.docsPageView, name='docs'),
    path("sign-in", views.loginView, name="login"),
    path("sign-out", views.logoutView, name="logout"),
    path("profile/<int:userId>", views.profilePageView, name="profile"),
    path("profile/edit/<int:userId>", views.editPageView, name="edit"),
    path("livedata", views.liveDataPageView, name="livedata"),
    path("global-map-view", views.mapView, name="mapview"),
    path("tools", views.ToolsPageView, name="tools"),
    path("analysis", views.analysisPageView, name="analysis")
]