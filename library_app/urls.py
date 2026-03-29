from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),   # ✅ first page
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),

    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:borrow_id>/', views.return_book, name='return_book'),

    # admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:borrow_id>/', views.approve_borrow, name='approve_borrow'),
    path('reject/<int:borrow_id>/', views.reject_borrow, name='reject_borrow'),
]