from django.contrib import admin
from .models import Customer, CustomerPowerlist, UserProfile


class CustomerPowerlistInline(admin.TabularInline):
    model = CustomerPowerlist
    extra = 1


class UserProfileInline(admin.TabularInline):
    model = UserProfile
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'created_at')
    search_fields = ('name', 'website')
    inlines = [CustomerPowerlistInline, UserProfileInline]


@admin.register(CustomerPowerlist)
class CustomerPowerlistAdmin(admin.ModelAdmin):
    list_display = ('customer', 'campaign_name', 'powerlist_id')
    list_filter = ('customer',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'customer')
    list_filter = ('customer',)
