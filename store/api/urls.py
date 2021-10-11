from django.urls import path
from .api_views import *

urlpatterns = [
    path('products/', ProductList.as_view(), name='products'),
    path('product/<str:slug>/', ProductDetail.as_view(), name='product_detail'),
    path('users/', UserList.as_view()),
    path('users/page/', UserDetail.as_view()),
    path('users/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/register/', UserRegistration.as_view(), name='register'),
    path('users/profile/', UserProfile.as_view(), name='profile'),
]
