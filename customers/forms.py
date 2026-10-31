
from django import forms
from .models import  Customer, Product 


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'price',
            'stock',
            'gst_rate',
            'description'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Enter price'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': 'Enter stock quantity'
            }),
            'gst_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Enter GST rate'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Optional description'
            }),
        }

    def clean_price(self):
        price = self.cleaned_data['price']

        if price <= 0:
            raise forms.ValidationError(
                'Price must be greater than 0.'
            )

        return price

    def clean_stock(self):
        stock = self.cleaned_data['stock']

        if stock < 0:
            raise forms.ValidationError(
                'Stock cannot be negative.'
            )

        return stock

    def clean_gst_rate(self):
        gst = self.cleaned_data['gst_rate']

        if gst < 0 or gst > 100:
            raise forms.ValidationError(
                'GST rate must be between 0 and 100.'
            )

        return gst
    
class InvoiceForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        empty_label="Select Customer",
        label="Customer"
    )
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="select Product",
        label="Product"
    )

    quantity = forms.IntegerField(
        min_value = 1,
        initial = 1,
        label = "Quantity"
    )