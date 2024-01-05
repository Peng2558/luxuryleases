from django.contrib import admin
from .models import Car, Rental, CreditCard, Store,Photo
# Register your models here.

admin.site.register(Car)
admin.site.register(Rental)
admin.site.register(CreditCard)
admin.site.register(Store)
admin.site.register(Photo)