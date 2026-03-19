from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('login/', views.signin_view, name='login'),
    path('signout/', views.signout_view, name='signout'),
    path('profile/', views.profile_view, name='profile'),
]
