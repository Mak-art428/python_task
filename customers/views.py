from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


from .models import Customer, Product, Invoice, InvoiceItem
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
    products_data = list(
        Product.objects.values('id', 'name', 'price', 'gst_rate')
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST)

        if form.is_valid():
            customer = form.cleaned_data['customer']

            product_ids = request.POST.getlist('product')
            quantities = request.POST.getlist('quantity')
            discount_rate = request.POST.get('discount', '0')

            try:
                discount_rate = Decimal(discount_rate)

                if discount_rate < 0 or discount_rate > 100:
                    raise ValueError

                if not product_ids or len(product_ids) != len(quantities):
                    raise ValueError

                invoice_items = []
                subtotal = Decimal('0.00')

                for product_id, quantity_value in zip(product_ids, quantities):
                    product = Product.objects.get(id=product_id)
                    quantity = int(quantity_value)

                    if quantity < 1:
                        raise ValueError

                    item_subtotal = product.price * quantity
                    subtotal += item_subtotal

                    invoice_items.append({
                        'product': product,
                        'quantity': quantity,
                        'subtotal': item_subtotal
                    })

                discount_amount = subtotal * discount_rate / Decimal('100')
                taxable_amount = subtotal - discount_amount

                total_gst = Decimal('0.00')

                for item in invoice_items:
                    item_discount = (
                        discount_amount * item['subtotal'] / subtotal
                        if subtotal > 0 else Decimal('0.00')
                    )

                    taxable_item = item['subtotal'] - item_discount

                    total_gst += (
                        taxable_item * item['product'].gst_rate
                        / Decimal('100')
                    )

                grand_total = taxable_amount + total_gst

                with transaction.atomic():
                    invoice = Invoice.objects.create(
                        customer=customer,
                        invoice_number=f"INV-{uuid4().hex[:10].upper()}",
                        total_amount=grand_total
                    )

                    for item in invoice_items:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            product=item['product'],
                            quantity=item['quantity'],
                            unit_price=item['product'].price,
                            subtotal=item['subtotal']
                        )

                messages.success(
                    request,
                    f'Invoice {invoice.invoice_number} created successfully!'
                )

                return redirect('create_invoice')

            except (ValueError, InvalidOperation, Product.DoesNotExist):
                messages.error(
                    request,
                    'Please select valid products, quantities and discount.'
                )

    else:
        form = InvoiceForm()

    return render(
        request,
        'customers/create_invoice.html',
        {
            'form': form,
            'products_data': products_data
        }
    )

def generate_invoice_pdf(request, id):
    invoice = get_object_or_404(Invoice, id=id)

    template_path = 'customers/invoice_pdf.html'
    context = {
        'invoice': invoice,
        'items': invoice.items.all(),
    }

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    )

    pdf_status = pisa.CreatePDF(html, dest=response)

    if pdf_status.err:
        return HttpResponse('Error while generating PDF')

    return response

def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-id')

    return render(
        request,
        'customers/invoice_list.html',
        {
            'invoices': invoices
        }
    )