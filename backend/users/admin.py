from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name',
                    'is_subscribed')
    list_filter = ('is_subscribed', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {
            'fields': ('avatar', 'is_subscribed')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительные поля', {
            'fields': ('email', 'first_name', 'last_name', 'avatar',
                       'is_subscribed')
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
