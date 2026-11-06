from django.urls import path
from . import views


urlpatterns = [
    path('customers/', views.customer_list, name='customer_list'),   
    path('customers/update/<int:id>/', views.update_customer, name='update_customer'),
    path('customers/delete/<int:id>/', views.delete_customer, name='delete_customer'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/', views.product_list, name='product_list'),
    path('products/update/<int:id>/', views.update_product, name='update_product'),
    path('products/delete/<int:id>/', views.delete_product, name='delete_product'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),

    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    path('api/admin/register/', views.admin_register_api, name='admin_register_api'),
    path('register-admin/', views.admin_register_page, name='admin_register_page'),
    path('api/admin/forgot-password/', views.admin_forgot_password_api, name='admin_forgot_password_api'),

    path('api/admin/verify-otp/', views.admin_verify_otp_api, name='admin_verify_otp_api'),

    path('api/admin/reset-password/', views.admin_reset_password_api, name='admin_reset_password_api'),
]