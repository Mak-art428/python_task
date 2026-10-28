from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, Product
from .forms import ProductForm, InvoiceForm 


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

def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')

    return redirect('product_list')


def add_product(request):
    success = ''

    if request.method == 'POST':
        form = ProductForm(request.POST)

        if form.is_valid():
            form.save()
            form = ProductForm()
            success = 'Product added successfully!'
    else:
        form = ProductForm()

    return render(
        request,
        'customers/add_product.html',
        {
            'form': form,
            'success': success
        }
    )


def product_list(request):
    search = request.GET.get('search', '').strip()

    products = Product.objects.all().order_by('id')

    if search:
        products = products.filter(
            name__icontains=search
        ) | products.filter(
            category__icontains=search
        )

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'customers/product_list.html',
        {
            'page_obj': page_obj,
            'search': search
        }
    )


# Create your views here.
def update_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        'customers/update_product.html',
        {
            'form': form,
            'product': product
        }
    )

def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')

    return redirect('customer_list')

def create_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)

        if form.is_valid():
            customer  = form.cleaned_data['customer']
            products = form.cleaned_data['products']
            quantity = form.cleaned_data['quantity']

            return render(
                request,
                'customers/create_invoice.html',
                {
                    'form' : form,
                    'success' : 'Invoice created successfully!',
                    'customer' : customer,
                    'products' : products,
                    'quantity' : quantity
                }
            )
    else:
        form = InvoiceForm()

        return render(
            request,
            'customers/create_invoice.html',
            {
                'form' : form
            }
        )