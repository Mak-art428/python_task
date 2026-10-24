from django.urls import path
from . import views

urlpatterns = [
    path('customers/', views.customer_list, name='customer_list'),   
    path('customers/update/<int:id>/', views.update_customer, name='update_customer'),
    path('customers/delete/<int:id>/', views.delete_customer, name='delete_customer'),
    path('products/add/', views.add_product, name='add_product')
]