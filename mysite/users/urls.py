from django.urls import path 
from .import views
from django.contrib.auth import views as auth_views



urlpatterns=[
    path('register/',views.register,name='register'),
    path('email-verification/<str:uidb64>/<str:token>',views.email_verification,name='email-verification'),
    path('email-verification-sent/',views.email_verification_sent,name='email-verification-sent'),
    path('email-verification-success/',views.email_verification_success,name='email-verification-success'),
    path('email-verification-failed/',views.email_verification_failed,name='email-verification-failed'),


    path('login/',views.user_login,name='login'),
    path('logout/',views.user_logout,name='logout'),
    path('profile/',views.profile,name='profile'),

    # password reset url paths
    path('password-reset',auth_views.PasswordResetView.as_view(),name='password_rest'),
    path('password-reset-sent/done',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(),name='password_reset_confim'),
    path('password_reset_complete',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),

]