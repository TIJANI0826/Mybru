from django.contrib import admin
from .models import PickupLocation

from .models import DeliveryAddress

# Register PickupLocation in admin
@admin.register(PickupLocation)
class PickupLocationAdmin(admin.ModelAdmin):
	list_display = ('name', 'branch', 'city', 'address', 'delivery_fee')
	search_fields = ('name', 'branch', 'city', 'address')


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
	list_display = ('user', 'address_line1', 'city', 'is_default', 'created_at')
	search_fields = ('user__username', 'address_line1', 'city')
