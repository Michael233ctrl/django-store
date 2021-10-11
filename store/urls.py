from django.contrib.auth.views import LogoutView
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    path('', StoreView.as_view(), name='store'),
    path('category/<str:pk>/', GetCategoryView.as_view(), name='category'),
    path('products/<str:product_slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('update_item/', update_item, name='update_item'),
    path('process_order/', process_order, name='process_order'),
    path('logout/', LogoutView.as_view(next_page='store'), name='logout'),
    path('user-profile/', login_required(UserProfileView.as_view(), login_url='store'), name='user_profile'),
    path('order/<int:pk>/', login_required(OrderDetail.as_view(), login_url='store'), name='order_detail'),

    path('reset_password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
