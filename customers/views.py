from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


from .models import Customer, Product, Invoice, InvoiceItem


from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

import secrets
from datetime import timedelta
from django.utils import timezone

from .models import PasswordResetOTP

from django.core.mail import send_mail

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerializer
from .forms import CustomerForm, ProductForm, InvoiceForm

from datetime import datetime
from django.db.models import Sum


import cv2
import numpy as npq


from django.contrib.auth.decorators import login_required

@login_required(login_url='login_page')
def admin_dashboard(request):
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_invoices = Invoice.objects.count()

    total_sales = sum(
        invoice.total_amount
        for invoice in Invoice.objects.all()
    )

    context = {
        'total_customers': total_customers,
        'total_products': total_products,
        'total_invoices': total_invoices,
        'total_sales': total_sales,
    }

    return render(
        request,
        'customers/admin_dashboard.html',
        context
)

@login_required(login_url='login_page')
def reports_page(request):

    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    invoices = Invoice.objects.all().order_by('-id')

    if start_date or end_date:

        if not start_date or not end_date:
            messages.error(
                request,
                'Please select both start date and end date.'
            )

        else:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()

                if start > end:
                    messages.error(
                        request,
                        'Start date cannot be greater than end date.'
                    )
                else:
                    invoices = invoices.filter(
                        invoice_date__date__range=[start, end]
                    )

            except ValueError:
                messages.error(
                    request,
                    'Please select valid dates.'
                )

    total_invoices = invoices.count()

    total_sales = invoices.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    context = {
        'invoices': invoices,
        'total_sales': total_sales,
        'total_invoices': total_invoices,
        'total_products': Product.objects.count(),
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(
        request,
        'customers/reports.html',
        context
    )



def download_report_pdf(request):

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    invoices = Invoice.objects.all().order_by('-id')

    if start_date and end_date:
        invoices = invoices.filter(
            invoice_date__date__range=[start_date, end_date]
        )

    total_invoices = invoices.count()

    total_sales = invoices.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    template = get_template('customers/report_pdf.html')

    context = {
        'invoices': invoices,
        'total_invoices': total_invoices,
        'total_sales': total_sales,
        'start_date': start_date,
        'end_date': end_date,
    }

    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice_report.pdf"'

    pdf_status = pisa.CreatePDF(html, dest=response)

    if pdf_status.err:
        return HttpResponse('PDF generation failed!')

    return response


@login_required(login_url='login_page')
def customer_list(request):

    search = request.GET.get('search', '')

    customers = Customer.objects.all().order_by('id')

    if search:
        customers = customers.filter(name__icontains=search) | customers.filter(email__icontains=search) | customers.filter(phone_number__icontains=search)

    return render(request, 'customers/customer_list.html',
                   {'customers': customers,
                     'search': search
                    })


@login_required(login_url='login_page')
def update_customer(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)

        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('customer_list')

    else:
        form = CustomerForm(instance=customer)

    return render(
        request,
        'customers/update.html',
        {
            'form': form,
            'customer': customer
        }
    )


@login_required(login_url='login_page')
def delete_product(request, id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=id)
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    else:
        messages.error(request, 'Invalid request!')

    return redirect('product_list')


@login_required(login_url='login_page')
def add_product(request):
    success = ''

    if request.method == 'POST':
        form = ProductForm(request.POST)
        
        if form.is_valid():
            print("FORM VALID: True")
            form.save()
            form = ProductForm()
            success = 'Product added successfully!'
        else:
            print("FORM VALID: False")
            print("FORM ERRORS:", form.errors)

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

@login_required(login_url='login_page') 
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
@login_required(login_url='login_page')
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

@login_required(login_url='login_page')
def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')

    return redirect('customer_list')


@login_required(login_url='login_page')
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

                    # Generate and save QR code
                    qr_file = generate_invoice_qr(invoice)
                    invoice.qr_code.save(
                        f"invoice_{invoice.id}.png",
                        qr_file,
                        save=True
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

@login_required(login_url='login_page')
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-id')

    paginator = Paginator(invoices, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'customers/invoice_list.html',
        {
            'invoices': page_obj,
            'page_obj': page_obj
        }
    )

@login_required(login_url='login_page')
def generate_invoice_qr(invoice):
    product_summary = ""

    for item in invoice.items.all():
        product_summary += (
            f"\nProduct: {item.product.name}"
            f"\nQuantity: {item.quantity}"
            f"\nPrice: Rs. {item.unit_price}"
            f"\nSubtotal: Rs. {item.subtotal}\n"
        )

    qr_data = (
        f"Invoice Number: {invoice.invoice_number}\n"
        f"Customer Name: {invoice.customer.name}\n"
        f"Invoice Date: {invoice.invoice_date.strftime('%d-%m-%Y')}\n"
        f"Product Count: {invoice.items.count()}\n"
        f"Product Summary:\n{product_summary}"
        f"Total Bill: Rs. {invoice.total_amount}"
    )

    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    return ContentFile(
        buffer.getvalue(),
        name=f"invoice_{invoice.id}.png"
    )

def regenerate_all_invoice_qr():
    invoices = Invoice.objects.all()

    for invoice in invoices:
        qr_file = generate_invoice_qr(invoice)

        invoice.qr_code.save(
            f"invoice_{invoice.id}.png",
            qr_file,
            save=True
        )


@csrf_exempt
@require_POST
def admin_register_api(request):
    try:
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not all([full_name, email, username, password, confirm_password]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)

        if password != confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match.'
            }, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists.'
            }, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already exists.'
            }, status=400)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name,
            is_staff=True
        )

        return JsonResponse({
            'success': True,
            'message': 'Admin registered successfully.',
            'username': user.username
        }, status=201)

    except Exception:
        return JsonResponse({
            'success': False,
            'message': 'Registration failed. Please try again.'
        }, status=500)


def admin_register_page(request):
    return render(request, 'customers/admin_register.html')


@csrf_exempt
@require_POST
def admin_forgot_password_api(request):

    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({
            'success': False,
            'message': 'Email is required.'
        }, status=400)

    user = User.objects.filter(
        email__iexact=email,
        is_staff=True
    ).first()

    # Same response whether the account exists or not
    if user:
        PasswordResetOTP.objects.filter(
            user=user,
            is_verified=False
        ).delete()

        otp = str(secrets.randbelow(9000) + 1000)

        PasswordResetOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        send_mail(
             subject='Admin Password Reset OTP',
             message=f"""
             Hello {user.first_name},

               Your password reset OTP is: {otp}  

             This OTP is valid for 5 minutes.

             Please do not share this OTP with anyone.

             Thank you.
        """,
             from_email=None,
             recipient_list=[user.email],
             fail_silently=False,
        )

    return JsonResponse({
        'success': True,
        'message': 'If the admin account exists, password recovery instructions will be sent.'
    }, status=200)

@csrf_exempt
@require_POST
def admin_verify_otp_api(request):

    email = request.POST.get('email', '').strip()
    otp = request.POST.get('otp', '').strip()

    if not email or not otp:
        return JsonResponse({
            'success': False,
            'message': 'Email and OTP are required.'
        }, status=400)

    user = User.objects.filter(
        email__iexact=email,
        is_staff=True
    ).first()

    if not user:
        return JsonResponse({
            'success': False,
            'message': 'Invalid email or OTP.'
        }, status=400)

    otp_record = PasswordResetOTP.objects.filter(
        user=user,
        otp=otp,
        is_verified=False,
        expires_at__gt=timezone.now()
    ).order_by('-created_at').first()

    if not otp_record:
        return JsonResponse({
            'success': False,
            'message': 'Invalid or expired OTP.'
        }, status=400)

    otp_record.is_verified = True
    otp_record.save()

    return JsonResponse({
        'success': True,
        'message': 'OTP verified successfully.'
    }, status=200)

@csrf_exempt
@require_POST
def admin_reset_password_api(request):

    email = request.POST.get('email', '').strip()
    otp = request.POST.get('otp', '').strip()
    new_password = request.POST.get('new_password', '')

    if not email or not otp or not new_password:
        return JsonResponse({
            'success': False,
            'message': 'Email, OTP and new password are required.'
        }, status=400)

    if len(new_password) < 8:
        return JsonResponse({
            'success': False,
            'message': 'Password must be at least 8 characters.'
        }, status=400)

    user = User.objects.filter(
        email__iexact=email,
        is_staff=True
    ).first()

    if not user:
        return JsonResponse({
            'success': False,
            'message': 'Invalid password reset request.'
        }, status=400)

    otp_record = PasswordResetOTP.objects.filter(
        user=user,
        otp=otp,
        is_verified=True,
        expires_at__gt=timezone.now()
    ).order_by('-created_at').first()

    if not otp_record:
        return JsonResponse({
            'success': False,
            'message': 'Invalid or expired OTP. Please verify OTP first.'
        }, status=400)

    user.set_password(new_password)
    user.save()

    PasswordResetOTP.objects.filter(user=user).delete()

    return JsonResponse({
        'success': True,
        'message': 'Password reset successfully.'
    }, status=200)


@api_view(['POST'])
def customer_register_api(request):

    serializer = CustomerSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response({
            'message': 'Customer registered successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'message': 'Registration failed!',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def decode_qr(request):

    if request.method == 'POST' and request.FILES.get('qr_image'):

        image_file = request.FILES['qr_image']

        image_array = np.frombuffer(
            image_file.read(),
            np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid image file.'
            })

        detector = cv2.QRCodeDetector()

        qr_data, points, _ = detector.detectAndDecode(image)

        if qr_data:
            return JsonResponse({
                'status': 'success',
                'qr_data': qr_data
            })

        return JsonResponse({
            'status': 'error',
            'message': 'No QR code found in image.'
        })

    return JsonResponse({
        'status': 'error',
        'message': 'Please upload a QR code image.'
    })

@login_required(login_url='login_page')
def qr_decode_page(request):
    return render(request, 'customers/qr_decode.html')

@csrf_exempt
@require_POST
def admin_login_api(request):

    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')

    if not email or not password:
        return JsonResponse({
            'success': False,
            'message': 'Email and password are required.'
        }, status=400)

    user = User.objects.filter(
        email__iexact=email,
        is_staff=True
    ).first()

    if not user:
        return JsonResponse({
            'success': False,
            'message': 'Invalid email or password.'
        }, status=401)

    authenticated_user = authenticate(
        request,
        username=user.username,
        password=password
    )

    if authenticated_user is None:
        return JsonResponse({
            'success': False,
            'message': 'Invalid email or password.'
        }, status=401)
     
    login(request, authenticated_user)
    return JsonResponse({
        'success': True,
        'message': 'Admin login successful.'
    }, status=200)



@csrf_exempt
@require_POST
def distributor_login_api(request):

    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')

    if not email or not password:
        return JsonResponse({
            'success': False,
            'message': 'Email and password are required.'
        }, status=400)

    user = User.objects.filter(
        username=email,
        is_staff=False
    ).first()

    if not user or not hasattr(user, 'distributor_profile'):
        return JsonResponse({
            'success': False,
            'message': 'Invalid email or password.'
        }, status=401)

    authenticated_user = authenticate(
        request,
        username=user.username,
        password=password
    )

    if authenticated_user is None:
        return JsonResponse({
            'success': False,
            'message': 'Invalid email or password.'
        }, status=401)

    login(request, authenticated_user)
    return JsonResponse({
        'success': True,
        'message': 'Distributor login successful.'
    }, status=200)

@csrf_exempt
@require_POST
def logout_api(request):
    logout(request)

    return JsonResponse({
        'success': True,
        'message': 'Logout successful.'
    }, status=200)


def login_page(request):
    return render(request, 'customers/login.html')