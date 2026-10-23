from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer

def customer_list(request):

    search = request.GET.get('search', '')

    customers = Customer.objects.all().order_by('id')

    if search:
        customers = customers.filter(name__icontains=search) | customers.filter(email__icontains=search) | customers.filter(phone_number__icontains=search)

    return render(request, 'customers/customer_list.html',
                   {'customers': customers,
                     'search': search
                    })

def update_customer(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        customer.name = request.POST.get('name', '')
        customer.email = request.POST.get('email', '')
        customer.phone_number = request.POST.get('phone_number', '')
        customer.save()

        return redirect('customer_list')

    return render(
        request, 
        'customers/update.html',
        {'customer': customer}
    )

# Create your views here.
