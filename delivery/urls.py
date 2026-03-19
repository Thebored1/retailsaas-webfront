from django.urls import path
from . import views

urlpatterns = [
    path("signin/", views.delivery_login, name="delivery_login"),
    path("signout/", views.delivery_logout, name="delivery_logout"),
    path("", views.delivery_orders_list, name="delivery_orders"),
    path("orders/<int:order_id>/", views.delivery_order_detail, name="delivery_order_detail"),
]
