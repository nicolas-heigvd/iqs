from django.urls import path

from . import views

app_name = "iqs"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("geolayers/", views.GeolayerView.as_view(), name="geolayers"),
    path("geolayers/<int:pk>/", views.GeolayerDetailView.as_view(), name="geolayer_detail"),
    path('geolayers/<int:pk>/attributes/', views.AttributeView.as_view(), name='attributes'),
    path('geolayers/<int:geolayer_pk>/attributes/<int:attribute_pk>', views.AttributeDetailView.as_view(), name='attribute_detail'),
]
