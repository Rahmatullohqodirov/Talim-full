from django.contrib import admin
from .models import PaymentTransaction, Invoice

admin.site.register(PaymentTransaction)
admin.site.register(Invoice)
