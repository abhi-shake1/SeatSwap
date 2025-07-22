from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list-seat/', views.list_seat, name='list_seat'),
    path('browse-seats/', views.browse_seats, name='browse_seats'),
    path('seat/<int:seat_id>/', views.seat_detail, name='seat_detail'),
    path('payment/<int:exchange_id>/', views.payment, name='payment'),
    path('verify-pnr/', views.verify_pnr, name='verify_pnr'),
    path('admin/exchanges/', views.admin_exchanges, name='admin_exchanges'),
]
